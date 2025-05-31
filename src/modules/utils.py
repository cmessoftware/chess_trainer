# utils.py - Funciones auxiliares

import os
import itertools
import sys
import time


def get_valid_paths_from_env(var_names):
    """
    Receives a list of environment variable names, checks if they exist,
    validates their content as existing paths, and returns the valid paths.
    """
    valid_paths = []
    for var in var_names:
        path = os.environ.get(var)
        if path and os.path.exists(path):
            valid_paths.append(path)
    return valid_paths

def show_spinner_message(message):
    """
    Prints a message to the console with a spinner effect.
    """
    spinner = itertools.cycle(['⏳', '🔄', '⏭️', '➡️'])
    sys.stdout.write(f"\r{next(spinner)} {message}")
    sys.stdout.flush()

def normalize_score_cp(score_cp, cap=300):
    """
    Normaliza un score de centipawns a una escala de -100 a +100.
    
    - Un score de +cap o más se transforma en +100.
    - Un score de -cap o menos se transforma en -100.
    - Los scores intermedios se escalan linealmente.

    Args:
        score_cp (int or float): Evaluación en centipawns.
        cap (int): Valor máximo para normalizar. Default: 300 (3 peones)

    Returns:
        float: Score normalizado entre -100 y +100.
    """
    score_cp = max(min(score_cp, cap), -cap)
    return (score_cp / cap) * 100
