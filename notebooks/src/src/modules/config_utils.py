import os

def is_valid_path(path):
    if not path or not isinstance(path, str):
        return False
    if not os.path.isabs(path):
        return False
    return True

def get_valid_paths_from_env(env_var_names):
    """
    Given a list of environment variable names, retrieves their values as paths,
    validates them, and returns the valid paths. Prints an error for any invalid path.
    """
    valid_paths = []
    for var_name in env_var_names:
        path = os.environ.get(var_name)
        if not path:
            print(f"Error: Environment variable '{var_name}' is not set.")
            continue
        if not is_valid_path(path):
            print(f"Error: Path '{path}' from '{var_name}' is invalid.")
            continue
        if not os.path.exists(path):
            print(f"Error: Path '{path}' from '{var_name}' does not exist.")
            continue
        valid_paths.append(path)
    return valid_paths
