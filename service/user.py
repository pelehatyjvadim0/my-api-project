from repository.user import UserRepository, RepoDep, Cache, RepoPostDep, PostRepository, RepoRefreshDep, RefreshRepository
from models.user import UsersModel, PostModel, RefreshSessionModel
from schemas.user import SUserAdd, SUserRead, SUserSKillsRead, SUserAddSkill, SPostAdd, SPostInfo, SUserReadBase
from core.security import hash_password, verify_password
from auth import create_token
from core.exceptions import NameRepeatError, UserNotFoundError, SkillsNotFoundError, SkillInListNotFoundError, AuthError, SkillAlreadyInUser
from typing import List, Annotated
from fastapi import Depends
from sqlalchemy.exc import IntegrityError
import secrets 
from datetime import datetime, timedelta, timezone

class UserRegistrationService:
    def __init__(self, repo: RepoDep):
        self.repo = repo
        
    async def register(self, user: SUserAdd) -> SUserRead:
        new_user_dict = user.model_dump()
        new_user_dict['password'] = hash_password(new_user_dict['password'])
        new_user_dict['city_id'] = Cache.get_city_id(user.city)
        new_user_dict.pop('city')
        new_user_model = UsersModel(**new_user_dict)
        try:
            new_user_create = await self.repo.create_user(new_user_model)
        except IntegrityError:
            raise NameRepeatError(name= new_user_model.name)
        
        return SUserRead.model_validate(new_user_create)
    
    async def auth(self, user_name: str, user_password: str, token_service: 'ServiceToken'):
        user = await self.repo.get_user_by_name(user_name=user_name)

        if user is None:
            raise AuthError()
        
        password_verify = verify_password(plain_password=user_password, hashed_password=user.password)
        
        if not password_verify:
            raise AuthError()
        
        token = create_token(data= {'sub': user.name})
        
        refresh_model = await token_service.create_token(user_id=user.id)
    
        return {
            'access_token': token,
            'token_type': 'bearer',
            'refresh_token': refresh_model.refresh_token
        }
          
    
class UserReadService:
    def __init__(self, repo: RepoDep):
        self.repo = repo
            
    async def get_all_users(self) -> List[SUserRead]:
        users = await self.repo.get_all_users()
    
        return [SUserRead.model_validate(user) for user in users]
    
    async def get_one_user(self, user_data: int | str) -> SUserRead:
        if isinstance(user_data, int):
            user = await self.repo.get_one_user(user_id=user_data)
        else:
            user = await self.repo.get_user_by_name(user_name=user_data)
        
        if user is None:
            raise UserNotFoundError()
            
        return SUserRead.model_validate(user)
    
    async def get_user_skills(self, user_id: int) -> SUserSKillsRead:
        user = await self.repo.get_user_skills(user_id)
        if user == None:
            raise UserNotFoundError()
        return SUserSKillsRead.model_validate(user)
    
class UserRedService:
    def __init__(self, repo: RepoDep):
        self.repo = repo
        
    async def delete_user(self, user_id) -> None:
        await self.repo.delete_user(user_id=user_id)
        return 
    
    async def add_skill(self, user_id: int, skill: SUserAddSkill) -> SUserSKillsRead:
        if skill.skill in Cache._skills:
            try:
                user = await self.repo.add_skill_at_user(user_id=user_id, skill_name=skill.skill)
            except IntegrityError as e:
                raise SkillAlreadyInUser(skill_name=skill.skill)
            return SUserSKillsRead.model_validate(user)
        else: 
            raise SkillInListNotFoundError(skill_name=skill.skill)
        
class PostService:
    def __init__(self, user_repo: UserRepository, post_repo: PostRepository):
        self.user_repo = user_repo
        self.post_repo = post_repo
        
    async def add_post(self, user_id: int, post: SPostAdd) -> SPostInfo:
        user = await self.user_repo.get_one_user(user_id=user_id)
        
        if not user:
            raise UserNotFoundError()
        
        new_post = PostModel(**post.model_dump(),
                            user_fk=user_id)
        
        create_post = await self.post_repo.add_post(user_id=user_id, post=new_post)
        
        return SPostInfo(
            user=SUserReadBase.model_validate(user),
            content=create_post.content
        )
    
    async def get_all_posts(self) -> list[SPostInfo]:
        posts = await self.post_repo.get_all_posts()
        
        posts = [SPostInfo.model_validate(post) for post in posts]

        return posts 
    
class TokenService:
    def __init__(self, repo: RefreshRepository):
        self.repo = repo
        
    async def create_token(self, user_id: int) -> RefreshSessionModel:
        secret_token = secrets.token_urlsafe(64)
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        new_refresh_token = RefreshSessionModel(
            refresh_token=secret_token,
            expires_at=expires_at,
            user_id=user_id
        )
        refresh_token = await self.repo.create_token(token=new_refresh_token)
        return refresh_token
    
    async def refresh_token(self, old_refresh_token: str):
        session = await self.repo.get_token(token=old_refresh_token)
        
        if session is None:
            raise AuthError(detail='Пользователь не найден!')
        
        if session.expires_at < datetime.now(timezone.utc):
            await self.repo.delete_token(token=old_refresh_token)
            raise AuthError(detail='Рефреш Токен истёк')
        
        await self.repo.delete_token(token=old_refresh_token)
        
        from auth import create_token
        
        new_refresh_model = await self.create_token(user_id=session.user_id)
        new_access_token = create_token(data = {'sub': str(session.user_id)})
        
        return {
            'access_token': new_access_token,
            'refresh_token': new_refresh_model.refresh_token
        }
        
    async def delete_token(self, token: str):
        await self.repo.delete_token(token=token)
        return
        
def get_user_reg_service(repo: RepoDep) -> UserRegistrationService:
    return UserRegistrationService(repo)

def get_user_read_service(repo: RepoDep) -> UserReadService:
    return UserReadService(repo)

def get_user_redaction_service(repo: RepoDep) -> UserRedService:
    return UserRedService(repo)

def get_post_service(user_repo: RepoDep, post_repo: RepoPostDep) -> PostService:
    return PostService(user_repo, post_repo)

def get_token_service(repo: RepoRefreshDep) -> TokenService:
    return TokenService(repo=repo)

ServiceUserReg = Annotated[UserRegistrationService, Depends(get_user_reg_service)]
ServiceUserRead = Annotated[UserReadService, Depends(get_user_read_service)]
ServiceUserRedaction = Annotated[UserRedService, Depends(get_user_redaction_service)]
ServicePost = Annotated[PostService, Depends(get_post_service)]
ServiceToken = Annotated[TokenService, Depends(get_token_service)]