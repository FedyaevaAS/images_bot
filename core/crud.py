from sqlalchemy import select

from core.db import AsyncSessionLocal
from core.models import Image, User


async def get_user_by_telegram_id(telegram_id):
    async with AsyncSessionLocal() as session:
        user = await session.execute(
            select(User).where(
                User.id == telegram_id
            )
        )
        user = user.scalars().first()
    return user


async def create_and_get_user(telegram_id):
    async with AsyncSessionLocal() as session:
        user = User(id=telegram_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def create_image(user, image):
    async with AsyncSessionLocal() as session:
        try:
            db_obj_image = Image(**image)
            session.add(db_obj_image)
            db_obj_image.users.append(user)
            await session.commit()
        except Exception:
            pass


async def get_photo_by_user(telegram_id):
    async with AsyncSessionLocal() as session:
        photos = await session.execute(
            select(
                Image
            )
            .join(Image.users)
            .where(User.id == telegram_id)
        )
        photos = photos.scalars().all()
    return photos


async def get_photo_by_id(id):
    async with AsyncSessionLocal() as session:
        photo = await session.execute(
            select(Image).where(
                Image.id == id
            )
        )
        photo = photo.scalars().first()
    return photo


async def delete(photo):
    async with AsyncSessionLocal() as session:
        await session.delete(photo)
        await session.commit()
