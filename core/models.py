from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from core.db import Base


class User(Base):
    id = Column(BigInteger, primary_key=True)
    images = relationship(
        'Image',
        secondary='userimage',
        back_populates='users'
    )


class Image(Base):
    id = Column(Integer, primary_key=True)
    author = Column(String(100), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    url = Column(String(150), unique=True, nullable=False)
    download_url = Column(String(150), unique=True, nullable=False)
    users = relationship(
        'User',
        secondary='userimage',
        back_populates='images'
    )

    def __str__(self):
        return f'{self.author} ({self.id})'


class UserImage(Base):
    id = Column(Integer, primary_key=True)
    user_telegram_id = Column(Integer, ForeignKey('user.id'))
    image_id = Column(Integer, ForeignKey('image.id'))
