from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Column
from database import Model
from typing import List

user_skills = Table(
    'user_skills',
    Model.metadata,
    Column('user_id', ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('skill_id', ForeignKey('skills.id'), primary_key=True)
)

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