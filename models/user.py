from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Column, Enum, String, DateTime, func
from database import Model
from typing import List
import enum
from datetime import datetime, timezone

user_skills = Table(
    'user_skills',
    Model.metadata,
    Column('user_id', ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('skill_id', ForeignKey('skills.id'), primary_key=True)
)

class UserRole(str, enum.Enum):
    ADMIN = 'admin'
    USER = 'user'

class UsersModel(Model):
    __tablename__= 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    age: Mapped[int] = mapped_column(nullable=False)
    city_id: Mapped[int] = mapped_column(ForeignKey('cities.id'), nullable=False)
    password: Mapped[str]
    
    city_obj: Mapped['CityModel'] = relationship(back_populates='user_list', init=False)
    
    skills_list: Mapped[List['SkillsModel']] = relationship(secondary=user_skills,
                                                            back_populates='user_list', 
                                                            init = False,
                                                            cascade='all, delete'
                                                            )
    
    posts: Mapped[list['PostModel']] = relationship(back_populates='author',
                                                    init = False)
    
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, nullable=False, init= False)
    
class CityModel(Model):
    __tablename__ = 'cities'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    city: Mapped[str] = mapped_column(nullable=False, unique=True)
    
    user_list: Mapped[List['UsersModel']] = relationship(back_populates='city_obj', init=False)
    
class SkillsModel(Model):
    __tablename__ = 'skills'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True)
    
    user_list: Mapped[List['UsersModel']] = relationship(secondary=user_skills,
                                                         back_populates='skills_list')
    
class PostModel(Model):
    __tablename__ = 'posts'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    content: Mapped[str] = mapped_column()
    user_fk: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    
    author: Mapped['UsersModel'] = relationship(back_populates='posts',
                                                init=False)
    
class RefreshSessionModel(Model):
    __tablename__ = 'refresh_tokens'
    
    id: Mapped[int] = mapped_column(primary_key=True, init= False)
    refresh_token: Mapped[str] = mapped_column(String, index=True, unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), init = False)