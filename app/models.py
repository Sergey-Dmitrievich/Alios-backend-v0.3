from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


# Тут везде модели для ДБ
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    name = Column(String)
    avatar_url = Column(String)
    password_hash = Column(String)

    chats = relationship('UserChat', back_populates='user')
    channels = relationship('UserChannel', back_populates='user')


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True, index=True)
    user_ids = Column(Text)  # Список идентификаторов пользователей в чате
    name = Column(String)  # Имя чата
    admin_id = Column(Integer, ForeignKey('users.id'))  # Администратор чата

    admin = relationship("User")  # Связь с моделью User


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    sender_id = Column(Integer, ForeignKey('users.id'))
    content = Column(Text)
    timestamp = Column(String)  # Можно использовать DateTime

class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"))
    avatar_url = Column(String)
    name = Column(String)  # Поле для имени канала

    admin = relationship("User")  # Связь с моделью User
    messages = relationship("ChannelMessage", back_populates="channel")  # Связь с моделью ChannelMessage
    members = relationship("ChannelMember", back_populates="channel")  # Связь с участниками канала


class UserChat(Base):
    __tablename__ = 'user_chats'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id'), primary_key=True)

class UserChannel(Base):
    __tablename__ = 'user_channels'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    channel_id = Column(Integer, ForeignKey('channels.id'), primary_key=True)





class ChannelMember(Base):
    __tablename__ = "channel_members"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)  # Добавлено поле для роли участника

    channel = relationship("Channel", back_populates="members")
    user = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    channel_id = Column(Integer, ForeignKey("channels.id"))
    message = Column(Text)
    read = Column(Boolean, default=False)

    user = relationship("User")
    channel = relationship("Channel")


class DirectMessage(Base):
    __tablename__ = "direct_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    
    content = Column(Text)
    media_url = Column(String, nullable=True)  # Новое поле для хранения URL медиафайла
    media_type = Column(String, nullable=True)  # Тип медиа (например, "image", "video", "gif")
    timestamp = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])


class ChannelMessage(Base):
    __tablename__ = "channel_messages"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    media_url = Column(String, nullable=True)  # Новое поле для хранения URL медиафайла
    media_type = Column(String, nullable=True)  # Тип медиа (например, "image", "video", "gif")
    timestamp = Column(DateTime, default=datetime.utcnow)

    channel = relationship("Channel", back_populates="messages")
    sender = relationship("User")

