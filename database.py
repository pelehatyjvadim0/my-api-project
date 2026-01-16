from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from typing import Annotated
from fastapi import Depends
from config import settings_db

engine = create_async_engine(settings_db.DATABASE_URL)
new_session = async_sessionmaker(bind=engine, expire_on_commit=False)

class Model(MappedAsDataclass, DeclarativeBase):
    pass

async def get_db():
    async with new_session() as session:
        yield session
        
SessionDep = Annotated[AsyncSession, Depends(get_db)]