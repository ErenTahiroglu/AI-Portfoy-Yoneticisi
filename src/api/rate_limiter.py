import time
import asyncio
import random
from functools import wraps
import logging
from .config import settings

logger = logging.getLogger(__name__)

class RateLimitException(Exception):
    pass

def with_retry(max_retries=None, base_delay=1.0, backoff_factor=None):
    """
    Exponential backoff with jitter retry decorator.
    Supports both sync and async functions.
    """
    if max_retries is None:
        max_retries = settings.MAX_RETRIES
    if backoff_factor is None:
        backoff_factor = settings.RETRY_BACKOFF_FACTOR
        
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                retries = 0
                delay = base_delay
                while True:
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        error_msg = str(e).lower()
                        is_rate_limit = any(x in error_msg for x in ["429", "rate limit", "too many requests", "quota", "timeout"])
                        
                        if not is_rate_limit and retries >= 1:
                            raise e
                            
                        if retries >= max_retries:
                            logger.error(f"Max retries ({max_retries}) reached for {func.__name__}")
                            raise RateLimitException(f"API Rate limit exceeded after {max_retries} retries: {str(e)}")
                        
                        jitter = random.uniform(0, 0.2 * delay)
                        sleep_time = delay + jitter
                        logger.warning(f"Rate limit/error in {func.__name__}: {e}. Retrying in {sleep_time:.2f}s (Attempt {retries+1}/{max_retries})")
                        await asyncio.sleep(sleep_time)
                        retries += 1
                        delay *= backoff_factor
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                retries = 0
                delay = base_delay
                while True:
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        error_msg = str(e).lower()
                        is_rate_limit = any(x in error_msg for x in ["429", "rate limit", "too many requests", "quota", "timeout"])
                        
                        if not is_rate_limit and retries >= 1:
                            raise e
                            
                        if retries >= max_retries:
                            logger.error(f"Max retries ({max_retries}) reached for {func.__name__}")
                            raise RateLimitException(f"API Rate limit exceeded after {max_retries} retries: {str(e)}")
                        
                        jitter = random.uniform(0, 0.2 * delay)
                        sleep_time = delay + jitter
                        logger.warning(f"Rate limit/error in {func.__name__}: {e}. Retrying in {sleep_time:.2f}s (Attempt {retries+1}/{max_retries})")
                        time.sleep(sleep_time)
                        retries += 1
                        delay *= backoff_factor
            return sync_wrapper
    return decorator
