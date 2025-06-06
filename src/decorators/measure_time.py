import time
from functools import wraps

def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"⏳ Ejecutando {func.__name__}...")
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"✅ {func.__name__} completada en {end - start:.2f} segundos")
        return result
    return wrapper


import time
from contextlib import contextmanager

@contextmanager
def timer(name="Bloque"):
    start = time.time()
    yield
    end = time.time()
    print(f"🕒 {name} tardó {end - start:.2f} segundos")

# Uso:
# with timer("Análisis completo"):
#     analyze_game_tactics()
