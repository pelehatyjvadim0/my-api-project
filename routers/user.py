from fastapi import APIRouter, status, Request, Depends
from fastapi.security import OAuth2PasswordRequestForm
from service.user import ServiceUserRead, ServiceUserReg, ServiceUserRedaction, ServicePost
from typing import List
from schemas.user import SUserAdd, SUserRead, SUserSKillsRead, SUserAddSkill, SPostInfo, SPostAdd, SAuthInfo
from core.redis import RedisDep
import json
from pydantic import TypeAdapter
from utils import cache_response, clean_cache, rate_limit
import asyncio
from auth import get_current_user


router = APIRouter(prefix='/users')

@router.post('/login', response_model=SAuthInfo)
async def login(service: ServiceUserReg, from_data: OAuth2PasswordRequestForm = Depends()):
    user = await service.auth(user_name=from_data.username, user_password=from_data.password)
    
    return user


@router.get('', status_code=status.HTTP_200_OK)
@rate_limit(limit=2, period=60)
@cache_response(expire=100, model=SUserRead)
async def get_all_users(service: ServiceUserRead, request: Request, token = Depends(get_current_user)) -> List[SUserRead]:
    
    users = await service.get_all_users()
    
    return users
          
@router.post('/create_user', status_code=status.HTTP_201_CREATED)
@clean_cache(get_all_users)
async def create_user(user: SUserAdd, service: ServiceUserReg) -> SUserRead:
    new_user = await service.register(user=user)
    
    return new_user

@router.get('/one_user/{user_id:int}', status_code=status.HTTP_200_OK)
@cache_response(expire=100, model=SUserRead)
async def get_user(user_id: int, service: ServiceUserRead) -> SUserRead:
    
    user = await service.get_one_user(user_data=user_id)

    return user
    
@router.get('/user_skills/{user_id:int}', status_code=status.HTTP_200_OK, response_model=SUserSKillsRead)
@cache_response(expire=100, model=SUserSKillsRead)
async def get_user_skills(user_id: int, service: ServiceUserRead):
    return await service.get_user_skills(user_id=user_id)

@router.delete('/del_user/{user_id:int}', status_code=status.HTTP_204_NO_CONTENT)
@clean_cache(get_all_users)
async def delete_user(user_id: int, service: ServiceUserRedaction):
    
    await service.delete_user(user_id=user_id)
    
    return

@router.post('/add_skill/{user_id:int}', status_code=status.HTTP_202_ACCEPTED, response_model=SUserSKillsRead)
@clean_cache(get_user_skills)
async def user_add_skill(user_id: int, skill: SUserAddSkill, service: ServiceUserRedaction):
    update_user = await service.add_skill(user_id=user_id, skill=skill)
    
    return update_user

@router.post('/{user_id:int}/create_post', status_code=status.HTTP_201_CREATED, response_model=SPostInfo)
async def create_post(user_id: int, post: SPostAdd, service: ServicePost):
    new_post = await service.add_post(user_id=user_id, 
                                      post=post)
    
    return new_post

@router.get('/posts/get_all', status_code=status.HTTP_200_OK, response_model=list[SPostInfo])
@cache_response(expire=60, model=SPostInfo)
async def get_all_posts(service: ServicePost):
    result = await service.get_all_posts()
    
    return result