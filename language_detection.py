from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound
from logging_config import logging

logger = logging.getLogger(__name__)


def _detect_language(code: str):
    try:
        lexer = guess_lexer(code)
        return lexer.name

    except ClassNotFound:
        logger.error('Language could not be determined.')
    except Exception as e:
        logger.error(f'An error occurred: {e}')


def should_process_file(filename: str, code: str) -> bool:
    """Check if file should be processed based on extension"""
    detected_language = _detect_language(code)
    if detected_language != 'Python':
        logger.warning(f'Unsupported language: {detected_language} in {filename}')
        return False
    return True
