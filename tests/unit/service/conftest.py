import pytest
from models.user import UsersModel

@pytest.fixture(scope='function')
async def m_repo(mocker):
    m_repo = mocker.AsyncMock()
    
    users = [
        {'id': 1, 'name': 'Гоша', 'age': 30, 'password': 'Gosha333'},
        {'id': 2, 'name': 'ПашаМАлой', 'age': 10, 'password': 'Pasha321'}
    ]
    
    m_repo.get_all_users.return_value = users
    m_repo.get_one_user.return_value = users[0]
    new_user = UsersModel(name='Боб', age=30, password='JAHFAJKSF123') 
    new_user.id = 1
    m_repo.create_user.return_value = new_user
    return m_repo