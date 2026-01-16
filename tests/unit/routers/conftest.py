import pytest
from main import app
from database import get_db
from service.user import get_user_read_service, get_user_reg_service, UserReadService, UserRegistrationService
from schemas.user import SUserRead, SUserAdd
from core.exceptions import NameRepeatError

@pytest.fixture(scope='function')
async def m_session(mocker):
    m_session = mocker.AsyncMock()
    app.dependency_overrides[get_db] = lambda: m_session
    
    yield m_session
    
    app.dependency_overrides.pop(get_db)
    
@pytest.fixture(scope='function')
async def m_service(mocker):
    m_service = mocker.AsyncMock(spec=UserReadService)
    app.dependency_overrides[get_user_read_service] = lambda: m_service
    
    users = [
        SUserRead(id=1, name='Егор', age=23),
        SUserRead(id=2, name='Владимир', age=40),
        SUserRead(id=3, name='Геннадий', age=35),
        SUserRead(id=4, name='Дмитрий Колёсик', age=17)
    ]
    
    async def find_user_id(user_id:int):
        for u in users:
            if u.id == user_id:
                return u
        return None
    
    m_service.get_all_users.return_value = users
    m_service.get_one_user.side_effect = find_user_id
    
    yield m_service
    
    app.dependency_overrides.pop(get_user_read_service)

@pytest.fixture(scope='function')    
async def m_reg_service(mocker):
    m_service = mocker.AsyncMock(spec=UserRegistrationService)
    app.dependency_overrides[get_user_reg_service] = lambda: m_service
    
    users = []
    
    async def reg_side_effect(user):
        
        for us in users:
            if us.name == user.name:
                raise NameRepeatError(name=user.name)
            
        new_user = SUserRead(
            id=len(users) + 1,
            name = user.name,
            age=user.age
        )

        users.append(new_user)
        return new_user
    
    m_service.register.side_effect = reg_side_effect
    
    yield m_service 
    
    app.dependency_overrides.pop(get_user_reg_service)
    
    
    