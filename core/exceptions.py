from fastapi import HTTPException, status

class BaseException(HTTPException):
    message = 'Произошла ошибка!'
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def __init__(self, detail: str | None = None):
        self.detail = detail or self.message
        super().__init__(status_code=self.status_code, 
                         detail=self.detail)
        
class NameRepeatError(BaseException):
    status_code = status.HTTP_409_CONFLICT
    
    def __init__(self, name: str, detail: str | None = None):
        self.custom_detail = detail or f'Ошибка! Имя | {name} | занято! Попробуйте другое!'
        super().__init__(detail=self.custom_detail)
        
class UserNotFoundError(BaseException):
    status_code = status.HTTP_404_NOT_FOUND
    
    def __init__(self):
        self.custom_detail = 'Пользователь не найден!'
        super().__init__(detail=self.custom_detail)
        
class SkillsNotFoundError(BaseException):
    status_code = status.HTTP_404_NOT_FOUND
    
    def __init__(self):
        self.custom_detail = 'У пользователя нет навыков!'
        super().__init__(detail=self.custom_detail)
        
class SkillInListNotFoundError(BaseException):
    status_code = status.HTTP_404_NOT_FOUND
    
    def __init__(self, skill_name: str):
        self.custom_detail = f'Переданный вами навык ({skill_name}) не зарегистрирован в базе!'
        super().__init__(detail=self.custom_detail)
        
class AuthError(BaseException):
    status_code = status.HTTP_401_UNAUTHORIZED
    
    def __init__(self):
        self.custom_detail = 'Логин или пароль не верны!'
        super().__init__(detail=self.custom_detail)
        
class SkillAlreadyInUser(BaseException):
    status_code = status.HTTP_409_CONFLICT
    
    def __init__(self, skill_name: str):
        self.custom_detail = f'Скилл {skill_name} уже есть в списке скиллов пользователя!'
        super().__init__(detail=self.custom_detail)
        