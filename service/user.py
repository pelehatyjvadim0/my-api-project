from repository.user import UserRepository, RepoDep, Cache, RepoPostDep, PostRepository
from models.user import UsersModel, PostModel
from schemas.user import SUserAdd, SUserRead, SUserSKillsRead, SUserAddSkill, SPostAdd, SPostInfo, SUserReadBase
from core.security import hash_password
from core.exceptions import NameRepeatError, UserNotFoundError, SkillsNotFoundError, SkillInListNotFoundError
from typing import List, Annotated
from fastapi import Depends
from sqlalchemy.exc import IntegrityError

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
    
class UserReadService:
    def __init__(self, repo: RepoDep):
        self.repo = repo
            
    async def get_all_users(self) -> List[SUserRead]:
        users = await self.repo.get_all_users()
    
        return [SUserRead.model_validate(user) for user in users]
    
    async def get_one_user(self, user_id: int) -> SUserRead:
        user = await self.repo.get_one_user(user_id=user_id)
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
            user = await self.repo.add_skill_at_user(user_id=user_id, skill_name=skill.skill)
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
        
def get_user_reg_service(repo: RepoDep) -> UserRegistrationService:
    return UserRegistrationService(repo)

def get_user_read_service(repo: RepoDep) -> UserReadService:
    return UserReadService(repo)

def get_user_redaction_service(repo: RepoDep) -> UserRedService:
    return UserRedService(repo)

def get_post_service(user_repo: RepoDep, post_repo: RepoPostDep) -> PostService:
    return PostService(user_repo, post_repo)

ServiceUserReg = Annotated[UserRegistrationService, Depends(get_user_reg_service)]
ServiceUserRead = Annotated[UserReadService, Depends(get_user_read_service)]
ServiceUserRedaction = Annotated[UserRedService, Depends(get_user_redaction_service)]
ServicePost = Annotated[PostService, Depends(get_post_service)]