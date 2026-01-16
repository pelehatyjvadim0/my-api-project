import pytest 
from httpx import ASGITransport, AsyncClient
from main import app
from core.exceptions import UserNotFoundError
from fastapi import HTTPException


@pytest.mark.get
async def test_get_all_users(m_session, m_service):
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
        response = await ac.get('/users')
    
    assert response.status_code == 200
    assert len(response.json()) == 4
    
@pytest.mark.get
@pytest.mark.parametrize('user_id, exc_status_code, exc_name', [
    (1, 200, 'Егор'),
    (3, 200, 'Геннадий'),
    (999, 404, None)
])
async def test_get_one_user(m_session, m_service, user_id, exc_status_code, exc_name):
    if exc_status_code == 404:
        m_service.get_one_user.side_effect = UserNotFoundError
        
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
        response = await ac.get(f'/users/one_user/{user_id}')
          
    if exc_status_code ==200:  
        assert response.json()['name'] == exc_name
    else:
        assert response.json()['detail'] == 'Пользователь не найден!'
       
@pytest.mark.post
@pytest.mark.parametrize('user, user2, exc_status_code1, exc_status_code2', [
    ({'name': 'Дралбаш Пишовин', 'age': 99, 'password': '123DRRD'},
     {'name': 'Павел Шпраузер', 'age': 33, 'password': '123DRRD'},
     201,
     201),
     ({'name': 'Павел Шпраузер', 'age': 33, 'password': '123DRRD'},
      {'name': 'Павел Шпраузер', 'age': 12, 'password': '123DRRD'},
     201,
     409),
     ({'name': 'Павел Шпраузер', 'age': 33, 'password': '123DRRD'},
      {'name': 'Павел Шпраузер', 'age': -1, 'password': '123DRRD'},
     201,
     422)
])
async def test_create_user(m_session, m_reg_service, user, user2, exc_status_code1, exc_status_code2):
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
        response1 = await ac.post('/users/create_user', json=user)
        response2 = await ac.post('/users/create_user', json=user2)
        
    assert response1.status_code == exc_status_code1
    assert response2.status_code == exc_status_code2
    
    if exc_status_code2 == 422:
        assert 'greater than or equal to 0' in response2.json()['detail'][0]['msg']
        
    
        
        
        
