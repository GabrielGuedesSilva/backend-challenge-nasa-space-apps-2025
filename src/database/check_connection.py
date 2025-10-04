import asyncpg

from src.utils.settings import Settings

settings = Settings()
db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')


async def check_database_connection():
    try:
        conn = await asyncpg.connect(db_url)
        await conn.close()
    except Exception:
        raise RuntimeError('Não foi possível conectar ao banco de dados')
