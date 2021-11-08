"""Store configuration in one place, and allow overriding it with environment variables"""

import os

def _try_env(key, default):
    """Gets the value of an environment variable, if it is set"""
    if key in os.environ:
        return os.environ[key]
    return default

def _parse_bool(encoded):
    """Parse a boolean string"""

    true_strings = ['true', '1', 't', 'y', 'yes']
    false_strings = ['false', '0', 'f', 'n', 'no']

    _encoded = encoded.lower()
    if _encoded in true_strings:
        return True
    if _encoded in false_strings:
        return False
    return None

def _try_env_bool(key, default):
    """Get an environment variable and parse it as a boolean"""
    encoded = _try_env(key, default)
    val = _parse_bool(encoded)
    if val is None:
        raise ValueError(
            f"Invalid value in {key} environment variable.\nMust be True or False."
        )
    return val

customer_config_dir = _try_env("CUSTOMER_CONFIG_DIR", "/customer_configs")
customer_prefix = _try_env("CUSTOMER_PREFIX", "")
create_secret_paths = _try_env_bool("CREATE_PATHS", "False")

vault_addr = _try_env("VAULT_ADDR", "")
vault_token = _try_env("VAULT_TOKEN", "")
vault_role_id = _try_env("VAULT_ROLE_ID", "")
vault_role_secret = _try_env("VAULT_ROLE_SECRET", "")

quiet = _try_env_bool("QUIET", "False")
verbose = _try_env_bool("VERBOSE", "True")

only_validate = _try_env_bool("ONLY_VALIDATE", "True")

invalid_group_prefix = _try_env("INVALID_GROUP_PREFIX", "")
