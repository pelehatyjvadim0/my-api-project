from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import pytest
from database import Model
from repository.user import UserRepository

@pytest.fixture(scope='session')
async def engine():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
        
    yield engine
    
    await engine.dispose()
        
@pytest.fixture(scope='function')
async def db_session(engine):
    
    connection = await engine.connect()
    
    transaction = await connection.begin()
    
    session_factory = async_sessionmaker(bind=connection,
                                         expire_on_commit=False)
    
    session = session_factory()
    
    yield session
    
    await session.close()
    await transaction.rollback()
    await connection.close()
    
@pytest.fixture(scope='function')
def UserRepo(db_session):
    user = UserRepository(session=db_session)
    return user