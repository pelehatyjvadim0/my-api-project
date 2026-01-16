import pytest
from service.user import UserReadService, UserRegistrationService
from core.exceptions import UserNotFoundError, NameRepeatError
from schemas.user import SUserAdd
from sqlalchemy.exc import IntegrityError

@pytest.mark.serviceread
async def test_get_all_users(m_repo):
    service = UserReadService(m_repo)
    
    result = await service.get_all_users()
    
    assert len(result) == 2
    assert not hasattr(result[0], 'password')

@pytest.mark.serviceread   
async def test_get_one_user(m_repo):
    service = UserReadService(m_repo)
    
    result = await service.get_one_user(user_id=1)
    
    assert result.name == 'Гоша'
    assert not hasattr(result, 'password')

@pytest.mark.serviceread    
async def test_get_one_user_not_found(m_repo):
    my_repo = m_repo
    my_repo.get_one_user.return_value = None
    
    service = UserReadService(my_repo)
    
    with pytest.raises(UserNotFoundError) as excinfo:
        result = await service.get_one_user(user_id = 1)
        
    assert excinfo.value.detail == 'Пользователь не найден!' 

@pytest.mark.servicereg   
@pytest.mark.parametrize('m_repo_result', [
    'giveError',
    'giveOK'
])
async def test_registr_new_user(m_repo, m_repo_result):
    
    if m_repo_result == 'giveError':
        m_repo.create_user.side_effect = IntegrityError(None, None, Exception())
        
        service = UserRegistrationService(m_repo)
    
        user = SUserAdd(name='Боб', age=30, password='JAHFAJKSF123')
        
        with pytest.raises(NameRepeatError) as excinfo:
            result = await service.register(user=user)
        
        args, kwargs = m_repo.create_user.call_args
        
        assert len(args) == 1
        assert args[0].name == 'Боб'
        assert args[0].password != 'JAHFAJKSF123'
        assert excinfo.value.detail == 'Ошибка! Имя | Боб | занято! Попробуйте другое!'
        
    else:
        service = UserRegistrationService(m_repo)
        
        user = SUserAdd(name='Боб', age=30, password='JAHFAJKSF123')
        
        result = await service.register(user=user)
        
        args, kwargs = m_repo.create_user.call_args
        
        assert not hasattr(result, 'password')
        assert len(args) == 1
        assert args[0].name == 'Боб'
        assert args[0].password != 'JAHFAJKSF123'