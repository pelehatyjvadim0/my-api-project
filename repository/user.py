from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload, selectinload
from abc import ABC, abstractmethod
from database import AsyncSession
from models.user import UsersModel, CityModel, SkillsModel, user_skills, PostModel
from fastapi import Depends
from typing import Annotated
from database import SessionDep
from typing import List
from core.exceptions import UserNotFoundError

class Cache:
    _cities: dict[str, int] = {}
    _skills: dict[str, int] = {}
    
    @classmethod
    def get_city_id(cls, cities_name: str) -> int:
        if cities_name in cls._cities:
            return cls._cities[cities_name]
        else:
            raise ValueError('Город не зарегистрирован!')
    
    @classmethod
    def get_skill_id(cls, skills_name: str) -> int:
        if skills_name in cls._skills:
            return cls._skills[skills_name]
        else:
            raise ValueError('Скилл не зарегистрирован!')
    
    @classmethod   
    async def update_cache(cls, session: AsyncSession):
        query = select(CityModel.id, CityModel.city)
        query2 = select(SkillsModel.id, SkillsModel.name)
        result_cities = await session.execute(query)
        result_skills = await session.execute(query2)
        data_cities = result_cities.all()
        data_skills = result_skills.all()
        cls._cities = {city: id for id, city in data_cities}
        cls._skills = {name: id for id, name in data_skills}
        
class BaseUserRepository(ABC):
    @abstractmethod
    async def create_user(self, user: UsersModel, session: AsyncSession):
        return NotImplemented
    
class UserRepository(BaseUserRepository):  
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_user(self, user: UsersModel) -> UsersModel:
        
        self.session.add(user)
        
        await self.session.commit()
        
        await self.session.refresh(user, attribute_names=['city_obj'])
        
        return user
    
    async def get_all_users(self) -> List[UsersModel]:
        query = select(UsersModel).options(joinedload(UsersModel.city_obj))
        
        result = await self.session.execute(query)
        
        return list(result.scalars().unique().all())
    
    async def get_one_user(self, user_id: int) -> UsersModel | None:
        query = select(UsersModel).options(joinedload(UsersModel.city_obj)).where(UsersModel.id == user_id)
        
        result = await self.session.execute(query)
        
        return result.scalar_one_or_none()
    
    async def get_user_by_name(self, user_name: str) -> UsersModel | None:
        query = select(UsersModel).options(joinedload(UsersModel.city_obj)).where(UsersModel.name == user_name)

        result = await self.session.execute(query)
        
        return result.scalar_one_or_none()
    
    async def get_user_skills(self, user_id: int) -> UsersModel | None:
        query = select(UsersModel).options(selectinload(UsersModel.skills_list)).where(UsersModel.id == user_id)
        
        result = await self.session.execute(query)
        
        return result.scalar_one_or_none()
    
    async def delete_user(self, user_id: int) -> None:
        query = delete(UsersModel).where(UsersModel.id == user_id)
        
        await self.session.execute(query)
        
        await self.session.commit()

        return
    
    async def add_skill_at_user(self, user_id: int, skill_name: str) -> UsersModel:
        query = select(UsersModel).options(selectinload(UsersModel.skills_list)).where(UsersModel.id == user_id)
        user = await self.session.execute(query)
        user = user.scalar_one_or_none()
        
        if not user:
            raise UserNotFoundError()
            
        query2 = select(SkillsModel).where(SkillsModel.name == skill_name)
        skill = await self.session.execute(query2)
        skill = skill.scalar_one()
        
        user.skills_list.append(skill)
        
        await self.session.commit()
        
        await self.session.refresh(user)
        
        return user
    
class PostRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def add_post(self, user_id: int, post: PostModel) -> PostModel: 
        self.session.add(post)
        
        await self.session.commit()
        
        await self.session.refresh(post)
        
        return post
    
    async def get_all_posts(self) -> List[PostModel]:
        query = select(PostModel).options(selectinload(PostModel.author))
        
        result = await self.session.execute(query)
        
        return list(result.scalars().all())
        
async def give_repo(session: SessionDep):
    return UserRepository(session)

async def give_post_repo(session: SessionDep):
    return PostRepository(session=session)

RepoDep = Annotated[UserRepository, Depends(give_repo)]
RepoPostDep = Annotated[PostRepository, Depends(give_post_repo)]
        