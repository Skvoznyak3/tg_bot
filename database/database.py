from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, create_engine, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

DATABASE_URL = "sqlite:///./bot_database.db"  # Укажите путь к вашей базе данных

# Настройка базы данных
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    timezone = Column(String, default="UTC")
    currency = Column(String, default="USD")

    favorites = relationship("Favorite", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ticker = Column(String, index=True)
    user = relationship("User", back_populates="favorites")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    period = Column(Integer, default=60)
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
    ticker = Column(String, index=True)
    type = Column(String, default="percentage")  # Например, "percentage" или "price_level"
    threshold = Column(Integer)  # Процент изменения или уровень цены для уведомления

    user = relationship("User", back_populates="subscriptions")


# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)