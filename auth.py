from fastapi import HTTPException, status, Depends
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from config import settings_jwt
from fastapi.security import OAuth2PasswordBearer
from database import get_db
from repository.user import RepoDep
from models.user import UsersModel, UserRole
    
def create_token(data: dict):
    to_encode = data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings_jwt.EXPIRE_TIME)
    
    to_encode.update({'exp': expire})
    
    jwt_token = jwt.encode(to_encode, settings_jwt.SECRET_KEY, algorithm=settings_jwt.ALGORITHM)
    
    return jwt_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='users/login')

async def get_current_user(repo: RepoDep, token: str = Depends(oauth2_scheme)):
    
    from service.user import UserReadService
    
    service = UserReadService(repo=repo)
    
    try:
        payload = jwt.decode(token, settings_jwt.SECRET_KEY, algorithms=[settings_jwt.ALGORITHM])
        
        username = payload.get('sub')
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Ошибка обработки токена. ID юзера не был получен!'
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Ошибка! Токен невалиден или истёк!'
        )
    
    return await service.get_one_user(user_data=username)

class RoleCheck:
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles
        
    async def __call__(self, user = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Недостаточно прав. Нобходимы: {self.allowed_roles}'
            )
        
        return user