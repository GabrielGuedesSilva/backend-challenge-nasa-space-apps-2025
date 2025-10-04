from src.background.scheduler import scheduler
from src.database.check_connection import check_database_connection
from src.utils.logger import logger


async def startup():
    try:
        await check_database_connection()
        logger.info('Conexão com o banco de dados estabelecida com sucesso.')

        scheduler.start()
        logger.info('Scheduler iniciado com sucesso.')

    except Exception as error:
        logger.error(f'Erro na inicialização: {error}')
        raise RuntimeError('Startup da aplicação interrompido.')


async def shutdown():
    scheduler.shutdown()
    logger.info('Encerrando a aplicação...')
