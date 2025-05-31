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
