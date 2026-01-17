from pydantic import BaseModel, Field, field_validator, ConfigDict, RootModel, AliasChoices
from enum import Enum
from typing import List
from repository.user import Cache

class OnCity(str, Enum):
    moscow = 'Москва'
    astrakhan = 'Астрахань'
    spb = 'Санкт-Петербург'
    sochi = 'Сочи'
    london = 'Лондон'
    
class DisplayNameStr(RootModel):
    root: str | None 
    
    @field_validator('root', mode='before')
    @classmethod
    def get_city_name(cls, v):
        if not isinstance(v, (str, int, dict, list, set, frozenset, float)):
            if hasattr(v, 'city'): return v.city
            if hasattr(v, 'name'): return v.name
            if hasattr(v, 'university'): return v.university
        return v 
        
    model_config = ConfigDict(from_attributes=True)
    

class SUserBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=20)
    age: int = Field(..., ge=0, le=100)
    
class SUserReadBase(BaseModel):
    id: int
    name: str
    
    model_config = ConfigDict(from_attributes=True)
    
class SUserAdd(SUserBase): 
    password: str
    city: OnCity
    
    @field_validator('password')
    @classmethod
    def password_validate(cls, v: str):
        if not any(item.isupper() for item in v):
            raise ValueError('Пароль должен содержать как минимум одну заглавную букву!')
        if not any(item.isdigit() for item in v):
            raise ValueError('Пароль должен содержать как минимум одну цифру!')
        if len(v) < 5:
            needed = 5 - len(v)
            raise ValueError(f'Длина пароля не может быть меньше 5! Недостаточно символов в пароле. (Ещё {needed})')
        
        return v
    
class SUserRead(SUserBase):
    id: int
    city: DisplayNameStr = Field(validation_alias='city_obj')
    role: str 
    
    model_config = ConfigDict(populate_by_name=True,
                              from_attributes=True)

class SSkil(BaseModel):
    id: int
    name: str
    
    model_config = ConfigDict(from_attributes=True)
    
class SUserSKillsRead(BaseModel):
    id: int
    name: str
    skills_list: List[SSkil] | str
    
    @field_validator('skills_list', mode='before')
    @classmethod 
    def check_skills_list(cls, v) -> List[SSkil] | str:
        if not v or len(v) == 0:
            return 'У пользователя нет скиллов :с'
        return v
    
    model_config = ConfigDict(from_attributes=True)
    
class SUserAddSkill(BaseModel):
    skill: str
    
    model_config = ConfigDict(from_attributes=True)
    
class SPostAdd(BaseModel):
    content: str = Field(max_length=1000)
    
    model_config = ConfigDict(from_attributes=True)
    
class SPostInfo(BaseModel):
    user: SUserReadBase = Field(validation_alias=AliasChoices('user', 'author'))
    content: str
    
    model_config = ConfigDict(from_attributes=True)
    
class STokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    
    model_config = ConfigDict(from_attributes=True)