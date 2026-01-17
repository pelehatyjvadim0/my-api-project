from fastapi import APIRouter, status, Request, Depends, Response, Cookie, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from service.user import ServiceUserRead, ServiceUserReg, ServiceUserRedaction, ServicePost, ServiceToken
from typing import List
from schemas.user import SUserAdd, SUserRead, SUserSKillsRead, SUserAddSkill, SPostInfo, SPostAdd, STokenResponse
from core.redis import RedisDep
import json
from pydantic import TypeAdapter
from utils import cache_response, clean_cache, rate_limit
import asyncio
from auth import get_current_user, RoleCheck
from models.user import UserRole

only_admin = [UserRole.ADMIN]
MAX_AGE = 30 * 24 * 60 * 60

router = APIRouter(prefix='/users')

@router.post('/login', response_model=STokenResponse)
async def login(response: Response, service_reg: ServiceUserReg, service_token: ServiceToken,  from_data: OAuth2PasswordRequestForm = Depends()):
    tokens = await service_reg.auth(user_name=from_data.username, user_password=from_data.password, token_service=service_token)
    
    response.set_cookie(
        key='refresh_token',
        value=tokens['refresh_token'],
        httponly=True,
        secure=True,
        samesite='lax',
        max_age=MAX_AGE
    )
    
    return {
        'access_token': tokens['access_token'],
        'token_type': 'bearer'
    }

@router.post('/refresh', response_model=STokenResponse)
async def refresh_token(
    service: ServiceToken,
    response: Response,
    refresh_token: str = Cookie(None)
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Refresh token missing'
        )
        
    print(refresh_token)
    
    tokens = await service.refresh_token(refresh_token)
    
    response.set_cookie(
        key='refresh_token',
        value=tokens['refresh_token'],
        httponly=True,
        secure=True,
        samesite='lax',
        max_age=MAX_AGE
    )
    
    return {'access_token': tokens['access_token']}

@router.post('/logout')
async def logout(
    response: Response,
    service: ServiceToken,
    refresh_token = Cookie(None)
):
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Токен невалиден'
        )
        
    await service.delete_token(token=refresh_token)
    
    response.delete_cookie(
        key = 'refresh_token',
        httponly=True,
        secure=True,
        samesite='lax'
    )
    
    return {
        'status': 'ok',
        'msg': 'Вы успешно вышли из аккаунта'
    }

@router.get('', status_code=status.HTTP_200_OK)
@rate_limit(limit=5, period=20)
@cache_response(expire=100, model=SUserRead)
async def get_all_users(service: ServiceUserRead, request: Request) -> List[SUserRead]:
    
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
async def delete_user(user_id: int, service: ServiceUserRedaction, user = Depends(RoleCheck(only_admin))):
    
    await service.delete_user(user_id=user_id)
    
    return

@router.post('/add_skill', status_code=status.HTTP_202_ACCEPTED, response_model=SUserSKillsRead)
@clean_cache(get_user_skills)
async def user_add_skill(skill: SUserAddSkill, service: ServiceUserRedaction, user = Depends(get_current_user)):
    update_user = await service.add_skill(user_id=user.id, skill=skill)
    
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