from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String(50), nullable=False)
    description = Column(String(200), nullable=True)
    status = Column(String(10), default='pending')  # Новое поле для статуса задачи