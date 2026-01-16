from core.redis import client
import hashlib
from functools import wraps
from typing import Any
import json
from fastapi import Request, HTTPException, status

# Генератор ключей для наших данных в Redis

def cache_key_generator(func_name, *args, **kwargs):
    prefix = f'cache:{func_name}'
    
    filtered_args = [a for a in args if isinstance(a, (str, bool, float, int, str, dict, list, type(None)))]
    filtered_kwargs = {k:v for k,v in kwargs.items() if isinstance(v, (str, float, bool, int, str, dict, list, type(None)))}
    
    args_data = str(filtered_args) + str(sorted(filtered_kwargs.items()))
    
    hashed_args = hashlib.md5(args_data.encode()).hexdigest()
    
    return f'{prefix}:{hashed_args}'

# Обёртка для работы с Redis. Чтение/Запись.
# Обязательно используем wraps, чтобы FastAPI видел имя не обёртки, а самой функции роутера!

def cache_response(expire: int = 60, model: Any = None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = cache_key_generator(func.__name__, *args, **kwargs)
            
            cache_json = await client.get(cache_key)
            
            try:
                if cache_json != None:
                    cache_data = json.loads(cache_json)
                    
                    if model:
                        if isinstance(cache_data, list):
                            result = [model.model_validate(item) for item in cache_data]
                        elif isinstance(cache_data, dict):
                            result = model.model_validate(cache_data)
                            
                        return result
                    
                    print(f'WARNING, cache_data is STRING')
                    return cache_data
    
            except Exception as e:
                print(f'Redis Error during GET: {e}')
                
            data = await func(*args, **kwargs)
            
            try:
                if data != None:
                    serializable_data = data
                    
                    if hasattr(serializable_data, 'model_dump'):
                        serializable_data = serializable_data.model_dump() #type: ignore
                    
                    elif hasattr(serializable_data, '__iter__') and not isinstance(serializable_data, (str, dict)):
                        serializable_data = [
                            item.model_dump() if hasattr(item, 'model_dump') else item
                            for item in serializable_data
                        ]   
                        
                    await client.set(
                        cache_key,
                        json.dumps(serializable_data),
                        ex = expire
                    ) 
            except Exception as e:
                print(f'Redis Error during SET: {e}')
            
            return data
        return wrapper
    return decorator

async def redis_cache_clear(target: Any):
    func_name = target.__name__ if callable(target) else str(target)
    
    prefix = f'cache:{func_name}:*'
    
    cache_key = await client.keys(prefix)
    
    if cache_key != None:
        await client.delete(*cache_key)
        print(f'DELETE KEYS: Успешно! | Ключей удалено: {len(cache_key)}')
        
def clean_cache(target: Any):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            try:
                await redis_cache_clear(target=target)
            except Exception as e:
                print(f'REDIS: Ошибка очистки кеша: {e}')
                
            return result
        return wrapper
    return decorator

def rate_limit(limit: int, period: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get('request')
            print(f"DEBUG: Request object: {request}")
            
            if not request:
                return await func(*args, **kwargs)
            
            user_ip = request.client.host
            
            key = f'rate_limit:{func.__name__}:{user_ip}'
            
            current_count = await client.incr(key)
            print(f"DEBUG: Ключ: {key}, Текущий счетчик: {current_count}")
            
            if current_count == 1:
                await client.expire(key, period)
                
            if current_count > limit:
                raise HTTPException(
                    status_code= status.HTTP_429_TOO_MANY_REQUESTS,
                    detail= {
                        'error': 'Слишком много запросов!',
                        'retry_after': f'Попробуйте снова через: {await client.ttl(key)}c.'
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator