from typing import List, Optional
from fastapi import FastAPI
from .database import engine
from .models import Base
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas, database
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

app = FastAPI()

# Для генерации документации
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Функция для хэширования пароля
def hash_password(password: str):
    return pwd_context.hash(password)

# Создание сессии с базой данных
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Проверка, существует ли уже пользователь с таким номером телефона
    existing_user = db.query(models.User).filter(models.User.phone_number == user.phone_number).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    # Хэширование пароля перед сохранением
    hashed_password = hash_password(user.password)
    
    new_user = models.User(
        phone_number=user.phone_number,
        name=user.name,
        avatar_url=user.avatar_url,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
from jose import JWTError, jwt
from datetime import datetime, timedelta

import os
SECRET_KEY = os.urandom(32).hex()
  # Замените на свой секретный ключ
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Функция для создания токена
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Эндпоинт для аутентификации
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect phone number or password")
    
    access_token = create_access_token(data={"sub": user.phone_number})
    return {"access_token": access_token, "token_type": "bearer"}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db, phone_number: str):
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()


@app.post("/chats/", response_model=schemas.Chat)
def create_chat(chat: schemas.ChatCreate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Получаем ID пользователя, который создает чат
    creator = db.query(models.User).filter(models.User.phone_number == phone_number).first()
    if not creator:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Создание нового чата
    new_chat = models.Chat(
        user_ids=",".join(map(str, chat.user_ids)),  # Преобразуем список ID в строку
        name=chat.name,
        admin_id=creator.id  # Устанавливаем создателя как администратора
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat


@app.post("/chats/{chat_id}/messages/", response_model=schemas.Message)
def send_message(chat_id: int, message: schemas.Message, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    # Извлечение пользователя из токена
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Здесь можно добавить дополнительную логику, например, проверку, что пользователь состоит в чате
    new_message = models.Message(
        chat_id=chat_id,
        sender_id=int(phone_number),  # Преобразуйте номер в ID пользователя
        content=message.content
    )
    
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

@app.post("/channels/", response_model=schemas.Channel)
def create_channel(channel: schemas.ChannelCreate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    # Извлечение пользователя из токена
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Создание нового канала
    new_channel = models.Channel(admin_id=int(phone_number), avatar_url=channel.avatar_url)
    db.add(new_channel)
    db.commit()
    db.refresh(new_channel)
    return new_channel

@app.post("/channels/{channel_id}/messages/", response_model=schemas.ChannelMessage)
def send_channel_message(channel_id: int, message: schemas.ChannelMessage, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    # Извлечение пользователя из токена
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Создание нового сообщения в канале
    new_message = models.ChannelMessage(
        channel_id=channel_id,
        sender_id=int(phone_number),  # Преобразуйте номер в ID пользователя
        content=message.content
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

@app.get("/channels/", response_model=List[schemas.Channel])
def get_channels(db: Session = Depends(get_db)):
    channels = db.query(models.Channel).all()
    return channels
@app.get("/channels/{channel_id}/messages/", response_model=List[schemas.ChannelMessage])
def get_channel_messages(channel_id: int, db: Session = Depends(get_db)):
    messages = db.query(models.ChannelMessage).filter(models.ChannelMessage.channel_id == channel_id).all()
    if not messages:
        raise HTTPException(status_code=404, detail="Этого канала не существует.")
    return messages

@app.post("/channels/{channel_id}/members/", response_model=schemas.ChannelMember)
def add_member(channel_id: int, user_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    # Проверка, является ли пользователь администратором канала
    # (Добавьте свою логику проверки, если это необходимо)
    
    new_member = models.ChannelMember(channel_id=channel_id, user_id=user_id)
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member

@app.delete("/channels/{channel_id}/members/{user_id}/")
def remove_member(channel_id: int, user_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    member = db.query(models.ChannelMember).filter(models.ChannelMember.channel_id == channel_id, models.ChannelMember.user_id == user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    db.delete(member)
    db.commit()
    return {"detail": "Member removed successfully"}

@app.get("/channels/{channel_id}/members/", response_model=List[schemas.ChannelMember])
def get_channel_members(channel_id: int, db: Session = Depends(get_db)):
    members = db.query(models.ChannelMember).filter(models.ChannelMember.channel_id == channel_id).all()
    return members

@app.post("/notifications/", response_model=schemas.Notification)
def create_notification(notification: schemas.NotificationCreate, db: Session = Depends(get_db)):
    new_notification = models.Notification(**notification.dict())
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification

@app.get("/notifications/{user_id}/", response_model=List[schemas.Notification])
def get_notifications(user_id: int, db: Session = Depends(get_db)):
    notifications = db.query(models.Notification).filter(models.Notification.user_id == user_id).all()
    return notifications

@app.get("/channels/search/", response_model=List[schemas.Channel])
def search_channels(query: str, db: Session = Depends(get_db)):
    channels = db.query(models.Channel).filter(models.Channel.name.ilike(f"%{query}%")).all()
    return channels

@app.put("/channels/{channel_id}/members/{user_id}/role/")
def update_member_role(channel_id: int, user_id: int, role: str, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    member = db.query(models.ChannelMember).filter(models.ChannelMember.channel_id == channel_id, models.ChannelMember.user_id == user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.role = role
    db.commit()
    return {"detail": "Member role updated successfully"}


@app.post("/messages/direct/", response_model=schemas.DirectMessage)
def send_direct_message(message: schemas.DirectMessageCreate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    new_message = models.DirectMessage(**message.dict())
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message


@app.get("/messages/direct/{user_id}/", response_model=List[schemas.DirectMessage])
def get_direct_messages(user_id: int, db: Session = Depends(get_db)):
    messages = db.query(models.DirectMessage).filter(
        (models.DirectMessage.sender_id == user_id) | (models.DirectMessage.receiver_id == user_id)
    ).all()
    return messages


from fastapi import WebSocket, WebSocketDisconnect

# Хранение подключенных пользователей
active_connections: dict = {}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    active_connections[user_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            # Здесь обрабатывать входящие сообщения
            await send_message_to_user(user_id, data)
    except WebSocketDisconnect:
        del active_connections[user_id]

async def send_message_to_user(user_id: int, message: str):
    # Логика для отправки сообщения другим пользователям
    for connection_user_id, connection in active_connections.items():
        if connection_user_id != user_id:
            await connection.send_text(f"User {user_id}: {message}")


from fastapi import WebSocket, WebSocketDisconnect
from collections import defaultdict





class WebSocketManager:
    async def handle_message(channel_id: int, sender_id: int, message: str, db: Session):
    # Сохранение сообщения в базе данных
        new_message = models.ChannelMessage(channel_id=channel_id, sender_id=sender_id, content=message)
        db.add(new_message)
        db.commit()
        await manager.broadcast_channel_message(channel_id, message, sender_id)

    def __init__(self):
        self.active_connections: dict = defaultdict(list)  # Словарь для хранения соединений по пользователям

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        self.active_connections[user_id].remove(websocket)

    async def send_personal_message(self, user_id: int, message: str):
        for connection in self.active_connections[user_id]:
            await connection.send_text(message)

    async def broadcast_channel_message(self, channel_id: int, message: str, sender_id: int):
        for user_id, connections in self.active_connections.items():
            # Здесь можно добавить проверку на то, является ли user_id членом канала
            for connection in connections:
                await connection.send_text(f"Channel {channel_id} | User {sender_id}: {message}")
                

manager = WebSocketManager()

@app.websocket("/ws/chat/{user_id}")
async def chat_websocket(websocket: WebSocket, user_id: int):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Обработка личных сообщений
            await manager.send_personal_message(user_id, data)
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)

@app.websocket("/ws/channel/{channel_id}/{user_id}")
async def channel_websocket(websocket: WebSocket, channel_id: int, user_id: int):
    await manager.join_channel(user_id, channel_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Обработка сообщений для канала
            await manager.broadcast_channel_message(channel_id, data, user_id)
    except WebSocketDisconnect:
        manager.leave_channel(user_id, channel_id)

@app.websocket("/ws/create_channel/{admin_id}")
async def create_channel_websocket(websocket: WebSocket, admin_id: int):
    await websocket.accept()
    try:
        while True:
            channel_name = await websocket.receive_text()
            # Логика создания канала
            # Например, сохранение канала в базе данных и уведомление об успешном создании
            await websocket.send_text(f"Channel '{channel_name}' created successfully by User {admin_id}.")
    except WebSocketDisconnect:
        pass


@app.get("/channels/{channel_id}/messages/", response_model=List[schemas.ChannelMessage])
def get_channel_messages(channel_id: int, db: Session = Depends(get_db)):
    messages = db.query(models.ChannelMessage).filter(models.ChannelMessage.channel_id == channel_id).order_by(models.ChannelMessage.timestamp).all()
    return messages

@app.get("/messages/direct/{user_id}/", response_model=List[schemas.DirectMessage])
def get_direct_messages(user_id: int, db: Session = Depends(get_db)):
    messages = db.query(models.DirectMessage).filter(
        (models.DirectMessage.sender_id == user_id) | (models.DirectMessage.receiver_id == user_id)
    ).order_by(models.DirectMessage.timestamp).all()
    return messages

@app.put("/chats/{chat_id}/", response_model=schemas.Chat)
def update_chat(chat_id: int, chat: schemas.ChatUpdate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Получаем ID пользователя, который делает запрос
    user = db.query(models.User).filter(models.User.phone_number == phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    chat_to_update = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat_to_update:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Проверяем, является ли пользователь администратором
    if chat_to_update.admin_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this chat")

    chat_to_update.name = chat.name
    db.commit()
    db.refresh(chat_to_update)
    return chat_to_update

@app.post("/chats/{chat_id}/admins/")
def add_admin(chat_id: int, user_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Получаем ID пользователя, который делает запрос
    user = db.query(models.User).filter(models.User.phone_number == phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Проверяем, является ли пользователь администратором
    if chat.admin_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add admins to this chat")

    # Здесь можно добавить логику для сохранения нового администратора
    # Например, запись в таблицу администраторов чата

    return {"detail": f"User {user_id} added as admin to chat {chat_id}"}


@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.name = user.name
    db_user.avatar_url = user.avatar_url
    db.commit()
    db.refresh(db_user)
    return db_user
