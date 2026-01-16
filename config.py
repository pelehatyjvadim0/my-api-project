from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus

class DataBase_Settings(BaseSettings):
    USER: str = 'postgres'
    PASSWORD: str = '123456789'
    DB: str = 'postgres'
    HOST: str = 'postgres-db'
    PORT: int = 5432
    
    @property
    def DATABASE_URL(self):
        NEW_PASS = quote_plus(self.PASSWORD)
        return f'postgresql+asyncpg://{self.USER}:{NEW_PASS}@{self.HOST}:{self.PORT}/{self.DB}'
    
    model_config = SettingsConfigDict(env_file='.env',
                                      env_prefix='DB_',
                                      extra='ignore')

class JWT_Settings(BaseSettings):
    SECRET_KEY: str 
    EXPIRE_TIME: int = 30
    ALGORITHM: str = 'HS256'

    model_config = SettingsConfigDict(env_file='.env',
                                      env_prefix='JWT_',
                                      extra='ignore')
    
settings_db = DataBase_Settings()
settings_jwt = JWT_Settings() #type: ignore
