from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import sys
import shutil
from datetime import timedelta, datetime
from pathlib import Path
from typing import List
import time

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import get_db, engine
from backend.models import Base, UserDB, SiteContent, EventDB
from backend.schemas import UserCreate, User, Token, UserLogin, SiteContentCreate, SiteContentUpdate, SiteContentOut, UserProfileUpdate, UserProfile, EventBase, EventCreate, EventUpdate, Event, EventParticipantUpdate
from backend.auth import authenticate_user, create_access_token, get_current_active_user, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_admin_user

# Create tables
Base.metadata.create_all(bind=engine)

# Функция для проверки и создания таблиц
def check_and_create_tables():
    with engine.connect() as conn:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        print("Существующие таблицы:", existing_tables)
        
        # Проверяем наличие всех необходимых таблиц
        required_tables = ["users", "site_content", "events"]
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"Создаем отсутствующие таблицы: {missing_tables}")
            Base.metadata.create_all(bind=engine)
            print("Таблицы успешно созданы!")
        else:
            print("Все необходимые таблицы уже существуют")

# Вызываем функцию проверки таблиц
check_and_create_tables()

# Get the directory of the current file
BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="MeetHere API",
    description="API для управления пользователями и встречами",
    version="1.0.0"
)

# Монтируем статический каталог для доступа к фотографиям профиля
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "backend/static")), name="static")

# Получаем URL фронтенда и админки из переменных окружения
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")
ADMIN_URL = os.getenv("ADMIN_URL", "*")

# CORS Configuration - с поддержкой production URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем доступ с любого источника
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
@app.post("/api/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# User routes
@app.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    db_user_email = db.query(UserDB).filter(UserDB.email == user.email).first()
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username already exists
    db_user_name = db.query(UserDB).filter(UserDB.username == user.username).first()
    if db_user_name:
        raise HTTPException(status_code=400, detail="Username already taken")
        
    # Hash the password
    hashed_password = get_password_hash(user.password)
    
    try:
        db_user = UserDB(
            email=user.email,
            username=user.username,
            password=hashed_password,
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/users/", response_model=list[User])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: UserDB = Depends(get_current_active_user)
):
    users = db.query(UserDB).offset(skip).limit(limit).all()
    return users
    
@app.get("/users/me", response_model=User)
async def read_users_me(current_user: UserDB = Depends(get_current_active_user)):
    return current_user

@app.patch("/users/me", response_model=User)
async def update_user_info(
    user_data: dict, 
    db: Session = Depends(get_db), 
    current_user: UserDB = Depends(get_current_active_user)
):
    # Проверяем, что username не пустой
    if "username" in user_data and user_data["username"]:
        # Проверяем, что имя не занято другим пользователем
        existing_user = db.query(UserDB).filter(
            UserDB.username == user_data["username"], 
            UserDB.id != current_user.id
        ).first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        
        current_user.username = user_data["username"]
    
    # Обновляем другие поля, если они есть
    if "email" in user_data and user_data["email"]:
        # Проверяем, что email не занят
        existing_email = db.query(UserDB).filter(
            UserDB.email == user_data["email"], 
            UserDB.id != current_user.id
        ).first()
        
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        current_user.email = user_data["email"]
    
    db.commit()
    db.refresh(current_user)
    
    return current_user
    
@app.get("/users/{user_id}", response_model=User)
def read_user(
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: UserDB = Depends(get_current_active_user)
):
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# --- Эндпоинты для работы с профилем пользователя ---
# Эндпоинт для получения профиля пользователя
@app.get("/api/profile/", response_model=UserProfile)
async def get_user_profile(current_user: UserDB = Depends(get_current_active_user)):
    profile = {
        "birth_date": current_user.birth_date,
        "gender": current_user.gender,
        "interests": current_user.interests or [],
        "joined_groups": current_user.joined_groups or [],
        "onboarding_completed": current_user.onboarding_completed or False,
        "profile_photo": current_user.profile_photo
    }
    return profile

# Эндпоинт для обновления профиля пользователя
@app.patch("/api/profile/", response_model=UserProfile)
async def update_user_profile(
    profile_data: UserProfileUpdate, 
    db: Session = Depends(get_db), 
    current_user: UserDB = Depends(get_current_active_user)
):
    # Обновляем только предоставленные поля
    user_data = {}
    
    if profile_data.birth_date is not None:
        user_data["birth_date"] = profile_data.birth_date
    
    if profile_data.gender is not None:
        user_data["gender"] = profile_data.gender
    
    if profile_data.interests is not None:
        user_data["interests"] = profile_data.interests
    
    if profile_data.joined_groups is not None:
        user_data["joined_groups"] = profile_data.joined_groups
    
    if profile_data.onboarding_completed is not None:
        user_data["onboarding_completed"] = profile_data.onboarding_completed
        
    if profile_data.profile_photo is not None:
        user_data["profile_photo"] = profile_data.profile_photo
    
    # Обновляем пользователя в базе данных
    for key, value in user_data.items():
        setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    
    # Возвращаем обновленный профиль
    return {
        "birth_date": current_user.birth_date,
        "gender": current_user.gender,
        "interests": current_user.interests or [],
        "joined_groups": current_user.joined_groups or [],
        "onboarding_completed": current_user.onboarding_completed or False,
        "profile_photo": current_user.profile_photo
    }

# Эндпоинт для проверки статуса опросника
@app.get("/api/onboarding-status/")
async def check_onboarding_status(current_user: UserDB = Depends(get_current_active_user)):
    return {"completed": current_user.onboarding_completed or False}

# --- Админские эндпоинты ---
@app.get("/admin/users", response_model=List[User])
def admin_get_users(db: Session = Depends(get_db), admin: UserDB = Depends(get_current_admin_user)):
    return db.query(UserDB).all()

@app.get("/admin/users/{user_id}", response_model=User)
def admin_get_user(user_id: int, db: Session = Depends(get_db), admin: UserDB = Depends(get_current_admin_user)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.patch("/admin/users/{user_id}", response_model=User)
def admin_update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db), admin: UserDB = Depends(get_current_admin_user)):
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.username = user.username
    db_user.email = user.email
    db_user.password = get_password_hash(user.password)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/admin/users/{user_id}")
def admin_delete_user(user_id: int, db: Session = Depends(get_db), admin: UserDB = Depends(get_current_admin_user)):
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"detail": "User deleted"}

# --- Контент сайта (SiteContent) ---
@app.get("/admin/content", response_model=List[SiteContentOut])
def admin_get_content(db: Session = Depends(get_db), admin: UserDB = Depends(get_current_admin_user)):
    return db.query(SiteContent).all()

@app.get("/admin/content/{key}", response_model=SiteContentOut)
def admin_get_content_by_key(key: str, db: Session = Depends(get_db), admin: UserDB = Depends(get_current_admin_user)):
    content = db.query(SiteContent).filter(SiteContent.key == key).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content

@app.post("/admin/content", response_model=SiteContentOut)
def admin_create_content(content: SiteContentCreate, db: Session = Depends(get_db), admin: UserDB = Depends(get_current_admin_user)):
    db_content = SiteContent(key=content.key, value=content.value)
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    return db_content

@app.patch("/admin/content/{key}", response_model=SiteContentOut)
def admin_update_content(key: str, content: SiteContentUpdate, db: Session = Depends(get_db), admin: UserDB = Depends(get_current_admin_user)):
    db_content = db.query(SiteContent).filter(SiteContent.key == key).first()
    if not db_content:
        raise HTTPException(status_code=404, detail="Content not found")
    db_content.value = content.value
    db.commit()
    db.refresh(db_content)
    return db_content

@app.delete("/admin/content/{key}")
def admin_delete_content(key: str, db: Session = Depends(get_db), admin: UserDB = Depends(get_current_admin_user)):
    db_content = db.query(SiteContent).filter(SiteContent.key == key).first()
    if not db_content:
        raise HTTPException(status_code=404, detail="Content not found")
    db.delete(db_content)
    db.commit()
    return {"detail": "Content deleted"}

# Создаем папку для хранения фотографий профиля, если её нет
PROFILE_PHOTOS_DIR = Path("backend/static/profile_photos")
os.makedirs(PROFILE_PHOTOS_DIR, exist_ok=True)

# API для загрузки фото профиля
@app.post("/api/profile/photo", response_model=dict)
async def upload_profile_photo(
    photo: UploadFile = File(...),
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Проверка типа файла
    if not photo.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    # Генерируем имя файла на основе ID пользователя и расширения
    file_extension = photo.filename.split('.')[-1] if '.' in photo.filename else 'jpg'
    filename = f"user_{current_user.id}_profile.{file_extension}"
    file_path = PROFILE_PHOTOS_DIR / filename
    
    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)
    
    # Создаем URL для фотографии
    photo_url = f"/static/profile_photos/{filename}"
    
    # Сохраняем URL в поле profile_photo
    current_user.profile_photo = photo_url
    db.commit()
    
    return {"success": True, "photo_url": photo_url}

# --- Эндпоинты для работы с событиями ---
@app.post("/api/events/", response_model=Event)
async def create_event(
    event: EventCreate, 
    db: Session = Depends(get_db), 
    current_user: UserDB = Depends(get_current_active_user)
):
    db_event = EventDB(
        **event.model_dump(), 
        created_by=current_user.id,
        participants=[current_user.id]  # Создатель автоматически становится участником
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

# Получение списка мероприятий
@app.get("/api/events/", response_model=List[Event])
async def get_events(
    skip: int = 0, 
    limit: int = 100, 
    filter_type: str = None,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    query = db.query(EventDB).filter(EventDB.is_active == True)
    
    # Фильтрация по типу
    if filter_type == "my":
        # Мои мероприятия (созданные пользователем)
        query = query.filter(EventDB.created_by == current_user.id)
    elif filter_type == "joined":
        # Мероприятия, в которых участвует пользователь
        query = query.filter(EventDB.participants.contains([current_user.id]))
    elif filter_type == "upcoming":
        # Предстоящие мероприятия
        query = query.filter(EventDB.event_date >= datetime.utcnow())
    elif filter_type == "past":
        # Прошедшие мероприятия
        query = query.filter(EventDB.event_date < datetime.utcnow())
    
    # Сортировка по дате (сначала ближайшие)
    query = query.order_by(EventDB.event_date)
    
    events = query.offset(skip).limit(limit).all()
    return events

# Получение конкретного мероприятия
@app.get("/api/events/{event_id}", response_model=Event)
async def get_event(
    event_id: int, 
    db: Session = Depends(get_db)
):
    event = db.query(EventDB).filter(EventDB.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

# Обновление мероприятия
@app.patch("/api/events/{event_id}", response_model=Event)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    db_event = db.query(EventDB).filter(EventDB.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Проверка прав на редактирование
    if db_event.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to edit this event")
    
    # Обновляем только предоставленные поля
    update_data = event_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)
    
    db.commit()
    db.refresh(db_event)
    return db_event

# Удаление мероприятия
@app.delete("/api/events/{event_id}")
async def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    db_event = db.query(EventDB).filter(EventDB.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Проверка прав на удаление
    if db_event.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this event")
    
    # Мягкое удаление (deactivation)
    db_event.is_active = False
    db.commit()
    
    return {"message": "Event successfully deleted"}

# Присоединение к мероприятию
@app.post("/api/events/{event_id}/join")
async def join_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    db_event = db.query(EventDB).filter(EventDB.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Проверка, не присоединился ли пользователь уже
    if current_user.id in db_event.participants:
        return {"message": "Already joined this event"}
    
    # Проверка на максимальное количество участников
    if db_event.max_participants and len(db_event.participants) >= db_event.max_participants:
        raise HTTPException(status_code=400, detail="Event is full")
    
    # Добавляем пользователя в список участников
    db_event.participants.append(current_user.id)
    db.commit()
    
    return {"message": "Successfully joined the event"}

# Выход из мероприятия
@app.post("/api/events/{event_id}/leave")
async def leave_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    db_event = db.query(EventDB).filter(EventDB.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Проверка, присоединился ли пользователь
    if current_user.id not in db_event.participants:
        return {"message": "Not joined this event"}
    
    # Если пользователь - создатель, нельзя выйти
    if db_event.created_by == current_user.id:
        raise HTTPException(status_code=400, detail="Event creator cannot leave the event")
    
    # Удаляем пользователя из списка участников
    db_event.participants.remove(current_user.id)
    db.commit()
    
    return {"message": "Successfully left the event"}

# Загрузка изображения для мероприятия
@app.post("/api/events/{event_id}/image", response_model=dict)
async def upload_event_image(
    event_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    # Проверяем существование мероприятия
    db_event = db.query(EventDB).filter(EventDB.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Проверка прав на редактирование
    if db_event.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to edit this event")
    
    # Проверка типа файла
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    # Создаем папку для хранения изображений мероприятий
    EVENT_IMAGES_DIR = Path("backend/static/event_images")
    os.makedirs(EVENT_IMAGES_DIR, exist_ok=True)
    
    # Генерируем имя файла
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    filename = f"event_{event_id}_{int(time.time())}.{file_extension}"
    file_path = EVENT_IMAGES_DIR / filename
    
    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Обновляем URL изображения в базе данных
    image_url = f"/static/event_images/{filename}"
    db_event.image_url = image_url
    db.commit()
    
    return {"success": True, "image_url": image_url}

if __name__ == "__main__":
    import uvicorn
    # Get port from environment variable for Railway deployment
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
