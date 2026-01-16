from fastapi import FastAPI
from routers.user import router as UserRouter
from database import engine, Model
from contextlib import asynccontextmanager
from repository.user import Cache
from database import new_session
from config import settings_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
        
    print('База данных готова к работе!')
    
    try:
        async with new_session() as session:
            await Cache.update_cache(session=session)
        print('Список городов в базе обновлён!')
    except Exception as e:
        print(f'КРИТИЧЕСКАЯ ОШИБКА! Список городов не был обновлён! {e}')
        
    yield 
    
    print('Выключение сервера!')
    
app = FastAPI(lifespan=lifespan)
app.include_router(UserRouter)
