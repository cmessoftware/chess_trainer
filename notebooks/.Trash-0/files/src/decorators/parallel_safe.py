# modules/decorators/parallel_safe.py
import logging
from traceback import format_exc

logger = logging.getLogger("tactical_analysis")
logger.setLevel(logging.ERROR)

handler = logging.FileHandler("/app/src/logs/parallel_errors.log")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def execute_parallel_safe(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            tb = format_exc()
            logger.error(f"❌ Error en {func.__name__}: {e}\n{tb}")
            print(f"❌ Error en análisis paralelo: {e}")
            return None, None
    return wrapper
