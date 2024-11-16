from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

class UserCreate(BaseModel):
    phone_number: str
    name: str
    avatar_url: Optional[str] = None
    password: str

class User(BaseModel):
    id: int
    phone_number: str
    name: str
    avatar_url: Optional[str] = None

    class Config:
        orm_mode = True

class Message(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    content: str
    timestamp: str

class Chat(BaseModel):
    id: int
    user_ids: List[int]

class ChatCreate(BaseModel):
    user_ids: List[int]
    name: str  # Имя чата

class ChatUpdate(BaseModel):
    name: str  # Новое имя чата


class ChannelCreate(BaseModel):
    avatar_url: Optional[str] = None

class Channel(BaseModel):
    id: int
    admin_id: int
    avatar_url: Optional[str] = None

class ChannelMessage(BaseModel):
    id: int
    channel_id: int
    sender_id: int
    content: str
    timestamp: str

class ChannelMember(BaseModel):
    id: int
    channel_id: int
    user_id: int

    class Config:
        orm_mode = True
class NotificationCreate(BaseModel):
    user_id: int
    channel_id: int
    message: str

class Notification(BaseModel):
    id: int
    user_id: int
    channel_id: int
    message: str
    read: bool

    class Config:
        orm_mode = True
class ChannelMember(BaseModel):
    id: int
    channel_id: int
    user_id: int
    role: str  # Роль участника

    class Config:
        orm_mode = True
class DirectMessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    content: str


class ChannelMessageCreate(BaseModel):
    channel_id: int
    sender_id: int
    content: str
    media_url: str = None  # Опциональное поле для URL медиафайла
    media_type: str = None  # Опциональное поле для типа медиа

class ChannelMessage(ChannelMessageCreate):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class DirectMessage(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    timestamp: str


    class Config:
        orm_mode = True

        
