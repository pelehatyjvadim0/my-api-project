import pytest
from models.user import UsersModel

async def test_create_user(UserRepo):
    user = UsersModel(
        name='Бобик',
        age=20,
        password='hashed_password'
    )
    
    result = await UserRepo.create_user(user=user)
    
    assert hasattr(result, 'id')
    assert result.name == 'Бобик'
    
async def test_get_all_users(UserRepo):
    
    result = await UserRepo.get_all_users()
    
    assert isinstance(result, list)
    assert len(result) == 0    
    
async def test_get_one_user(UserRepo):
    
    result = await UserRepo.get_one_user(user_id=1)
    
    assert result == None
