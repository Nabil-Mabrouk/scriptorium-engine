# src/core/task_queue.py
from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

class TaskQueue:
    pool: ArqRedis = None
    # This will hold the correctly configured RedisSettings object
    redis_settings: RedisSettings = None

    @classmethod
    def configure(cls, redis_settings_url: str):
        """Configures the Redis settings from a URL. Does not connect."""
        # Use the correct 'from_dsn' method and store the object
        cls.redis_settings = RedisSettings.from_dsn(redis_settings_url)

    @classmethod
    async def connect(cls):
        """Initializes the connection pool to Redis."""
        if not cls.redis_settings:
            raise ConnectionError("TaskQueue is not configured. Call .configure() first.")
        cls.pool = await create_pool(cls.redis_settings)

    @classmethod
    async def close(cls):
        """Closes the connection pool."""
        if cls.pool:
            await cls.pool.close()

    @classmethod
    async def enqueue(cls, function_name: str, *args, **kwargs):
        """Enqueues a job to be run by a worker."""
        if not cls.pool:
            raise ConnectionError("TaskQueue is not connected. Call .connect() first.")
        return await cls.pool.enqueue_job(function_name, *args, **kwargs)

# A single instance to be used throughout the application
task_queue = TaskQueue()