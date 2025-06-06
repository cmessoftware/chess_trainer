
import functools
import logging
import inspect
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import time

# Crear directorio si no existe
os.makedirs("logs", exist_ok=True)

# Nivel configurable (default: INFO)
log_level = os.getenv("LOG_LEVEL", "INFO").upper()

# Configuración del logger
log_file = os.path.join(
    "logs", f"log_{datetime.now().strftime('%Y-%m-%d')}.txt"
)
handler = RotatingFileHandler(
    log_file, maxBytes=1_000_000, backupCount=5, mode="a"  # modo append
)

formatter = logging.Formatter(
    "📘 [%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)

logger = logging.getLogger("auto_logger")
logger.setLevel(log_level)
logger.addHandler(handler)
logger.propagate = False  # Evita duplicados si hay otros handlers globales

def log_function_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"🔍 Llamando: {func.__name__}({args}, {kwargs})")
        try:
            result = func(*args, **kwargs)
            if result is None or isinstance(result, (int, float, str, bool)):
                logger.info(f"✅ Resultado de {func.__name__}: {result}")
            else:
                logger.info(f"✅ Resultado de {func.__name__}: Objeto complejo")
            return result
        except Exception as e:
            logger.exception(f"❌ Excepción en {func.__name__}: {e}")
            raise
    return wrapper

def auto_log_module_functions(namespace):
    for name, obj in list(namespace.items()):
        if inspect.isfunction(obj) and not name.startswith("_"):
            namespace[name] = log_function_call(obj)
            
# modules/auto_logger.py

def auto_logger_execution_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        name = func.__name__
        print(f"▶ Running {name}...")
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = round(time.time() - start_time, 2)
            print(f"✔ {name} completed in {duration} seconds.")
            return result
        except Exception as e:
            duration = round(time.time() - start_time, 2)
            print(f"❌ {name} failed after {duration} seconds. Error: {e}")
            raise
    return wrapper

