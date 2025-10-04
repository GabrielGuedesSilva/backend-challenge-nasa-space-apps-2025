import sys

from loguru import logger


def setup_logger():
    def log_format(record):
        level_with_colon = f'{record["level"].name}:'
        padded_level = level_with_colon.ljust(9)
        return (
            f'<lvl>{padded_level}</lvl> '
            '{message} | '
            '<m>[{time:YYYY-MM-DD HH:mm:ss}]</m>\n'
        )

    logger.remove()
    logger.add(sys.stdout, format=log_format, level='INFO')

    logger.level('DEBUG', color='<blue>')
    logger.level('INFO', color='<green>')
    logger.level('WARNING', color='<yellow>')
    logger.level('ERROR', color='<red>')
    logger.level('CRITICAL', color='<red><bold>')

    return logger


setup_logger()
