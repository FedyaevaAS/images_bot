import csv
import io
from http import HTTPStatus

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (AIORateLimiter, ApplicationBuilder,
                          CallbackContext, CallbackQueryHandler,
                          CommandHandler, ContextTypes, ConversationHandler,
                          MessageHandler)
from telegram.ext.filters import TEXT

from core.config import settings
from core.crud import (create_and_get_user, create_image, delete,
                       get_photo_by_id, get_photo_by_user,
                       get_user_by_telegram_id)
from core.models import Image

(
    START_OVER,
    LINK,
    SELECTING_ACTION,
    ADD_PHOTOS,
    PHOTOS_LIST,
    GET_PHOTOS_TABLE,
    CHOSEN_PHOTO,
    BACK_TO_MENU,
    DELETE,
    BACK,
    ACTION_WITH_PHOTO,
    DELETE_CONFIRMATION,
) = map(chr, range(12))


KEYBOARDS = {
    'full_menu': [
        [
            InlineKeyboardButton(
                '➕ Добавить фотографии',
                callback_data=str(ADD_PHOTOS)
            ),
        ],
        [
            InlineKeyboardButton(
                '📃 Список фотографий',
                callback_data=str(PHOTOS_LIST)
            ),
        ],
        [
            InlineKeyboardButton(
                '📋 Получить таблицу фото',
                callback_data=str(GET_PHOTOS_TABLE)
            ),
        ],
    ],
    'get_back': [
        [InlineKeyboardButton('🔙 В меню', callback_data=str(BACK_TO_MENU)),]
    ],
    'yes_or_no': [
        [InlineKeyboardButton('✅ Да', callback_data=str(DELETE)),],
        [InlineKeyboardButton('❎ Нет', callback_data=str(BACK)),],
    ],
    'delete_or_back': [
        [
            InlineKeyboardButton(
                '🗑 Удалить',
                callback_data=str(DELETE_CONFIRMATION)
            ),
        ],
        [InlineKeyboardButton('🔙 Назад', callback_data=str(BACK))],
    ],
}


async def start(update: Update, context: CallbackContext):
    """Команда /start."""
    text = (
        'Привет, это онбординг.\nПришлите мне ссылку на '
        'список фотографий с picsum.photos, например: '
        'https://picsum.photos/v2/list?page=2&limit=100'
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        disable_web_page_preview=True
    )
    return LINK


async def url_handler(update: Update, context: CallbackContext):
    url = update.message.text

    try:
        response = requests.get(url)
        if response.status_code != HTTPStatus.OK:
            raise Exception
        user = await get_user_by_telegram_id(update.effective_chat.id)
        if user is None:
            user = await create_and_get_user(update.effective_chat.id)
        images = response.json()
        for image in images:
            await create_image(user, image)
        await update.message.reply_text('Фотографии успешно сохранены.')
    except Exception:
        if context.user_data.get(START_OVER):
            keyboard = KEYBOARDS['get_back']
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                text='Ссылка некорректна. Попробуйте еще раз.',
                reply_markup=reply_markup
            )
            return LINK
        else:
            await update.message.reply_text(
                'Ссылка некорректна. Вы можете добавить '
                'фотографии из меню по кнопке ниже.'
            )

    keyboard = KEYBOARDS['full_menu']
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Главное меню.', reply_markup=reply_markup)
    context.user_data[START_OVER] = True
    return SELECTING_ACTION


async def add_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        'Пришлите мне ссылку на список фотографий с picsum.photos, например: '
        'https://picsum.photos/v2/list?page=2&limit=100'
    )
    await update.callback_query.edit_message_text(
        text=text,
        disable_web_page_preview=True
    )
    return LINK


async def photos_list(update: Update, context: CallbackContext):
    photos = await get_photo_by_user(update.effective_chat.id)
    fields = Image.__mapper__.columns
    fields_to_csv = list(map(lambda x: x.name, fields))
    s = io.StringIO()
    csv.writer(s).writerow(fields_to_csv)
    for photo in photos:
        csv.writer(s).writerow(getattr(photo, field.name) for field in fields)
    s.seek(0)
    buf = io.BytesIO()
    buf.write(s.getvalue().encode())
    buf.seek(0)
    buf.name = 'images.csv'
    await update.callback_query.message.reply_document(
        buf,
        caption='Таблица с изображениями успешно сформирована.'
    )


async def get_photos_table(update: Update, context: CallbackContext):
    photos = await get_photo_by_user(update.effective_chat.id)
    keyboard = []
    for photo in photos:
        keyboard.append([
            InlineKeyboardButton(
                str(photo),
                callback_data=photo.id
            )
        ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        text='Список фотографий.',
        reply_markup=reply_markup
    )
    return CHOSEN_PHOTO


async def back_to_menu(update: Update, context: CallbackContext):
    keyboard = KEYBOARDS['full_menu']
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        text='Главное меню.',
        reply_markup=reply_markup
    )
    return SELECTING_ACTION


async def get_photo(update: Update, context: CallbackContext):
    photo_data = await get_photo_by_id(update.callback_query.data)
    keyboard = KEYBOARDS['delete_or_back']
    reply_markup = InlineKeyboardMarkup(keyboard)
    caption = (
        f'Author: {photo_data.author}\n'
        f'ID: {photo_data.id}\n'
        f'Size: {photo_data.width}x{photo_data.height}\n'
        f'URL: {photo_data.url}\n'
        f'Download URL: {photo_data.download_url}\n'
    )
    await update.callback_query.message.reply_photo(
        photo_data.download_url,
        caption=caption,
        reply_markup=reply_markup
    )
    context.user_data['id'] = photo_data.id
    context.user_data['author'] = photo_data.author
    return ACTION_WITH_PHOTO


async def delete_photo_confirmation(update: Update, context: CallbackContext):
    update.callback_query.message
    keyboard = KEYBOARDS['yes_or_no']
    reply_markup = InlineKeyboardMarkup(keyboard)
    id = context.user_data.get('id')
    author = context.user_data.get('author')
    caption = (
        'Вы уверены, что хотите удалить эту фотографию?\n'
        f'{author} {id}'
    )
    await update.callback_query.message.edit_caption(caption=caption)
    await update.callback_query.message.edit_reply_markup(
        reply_markup=reply_markup
    )


async def delete_photo(update: Update, context: CallbackContext):
    photo = await get_photo_by_id(context.user_data['id'])
    await delete(photo)
    await get_photos_table(update, context)


def create_bot():
    """Создать бота."""
    bot_instance = (
        ApplicationBuilder()
        .token(settings.bot_token)
        .rate_limiter(AIORateLimiter())
        .build()
    )
    get_photos = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            get_photos_table,
            pattern="^" + str(GET_PHOTOS_TABLE) + "$"
        )],
        states={
            CHOSEN_PHOTO: [CallbackQueryHandler(get_photo)],
            ACTION_WITH_PHOTO: [
                CallbackQueryHandler(
                    get_photos_table,
                    pattern="^" + str(BACK) + "$"
                ),
                CallbackQueryHandler(
                    delete_photo_confirmation,
                    pattern="^" + str(DELETE_CONFIRMATION) + "$"
                ),
                CallbackQueryHandler(
                    delete_photo,
                    pattern="^" + str(DELETE) + "$"
                ),
            ]
        },
        fallbacks=[],
    )
    selection_handlers = [
        CallbackQueryHandler(add_photos, pattern="^" + str(ADD_PHOTOS) + "$"),
        CallbackQueryHandler(
            photos_list,
            pattern="^" + str(PHOTOS_LIST) + "$"
        ),
        get_photos,
    ]
    start_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LINK: [
                MessageHandler(TEXT, url_handler),
                CallbackQueryHandler(
                    back_to_menu,
                    pattern="^" + str(BACK_TO_MENU) + "$"
                ),
            ],
            SELECTING_ACTION: selection_handlers,
        },
        fallbacks=[],
    )
    bot_instance.add_handler(start_conv)
    return bot_instance
