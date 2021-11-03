"""Main entrypoint to parse and apply customer configs."""
from glob import glob
from os import path

from . import parse, config, translate, hashivault, log

def get_customer_files():
    """Search customer config dir for .yml and .yaml files."""
    return [
        *glob(
            path.join(config.customer_config_dir, '*.yml')
        ),
        *glob(
            path.join(config.customer_config_dir, '*.yaml')
        ),
    ]

def parse_customer_configs(customer_files):
    """Parse and validate a list of customer config files."""
    customer_configs = []
    errors = []
    for customer_file in customer_files:
        # pylint: disable=broad-except
        try:
            customer_configs.append(parse.parse_file(customer_file))
        except Exception as err:
            errors.append(str(err))
    if len(errors) != 0:
        raise ValueError("Error(s) parsing customer configs:\n{e}".format(
            e="\n-----------\n".join(errors)
        ))
    return customer_configs

def apply_customer_configs(customer_configs):
    """Flatten/combine a list of customer configs and apply them to a vault server."""
    flat_configs = translate.flatten(customer_configs)
    try:
        return hashivault.apply_flat_config(
            groups=flat_configs['groups'],
            approles=flat_configs['approles'],
            policies=flat_configs['policies'],
            paths=flat_configs['paths'],
        )
    except Exception as err:
        raise Exception("Error applying customer config to vault server:\n{e}".format(
            e=err,
        )) from err

def main():
    """Apply a directory of customer config files to a vault server."""
    log.debug(f"Scanning customer dir {config.customer_config_dir}")
    customer_files = get_customer_files()
    log.debug("Found files:\n{files}".format(
        files="\n".join(customer_files)
    ))
    customer_configs = parse_customer_configs(
        get_customer_files()
    )
    if not config.only_validate:
        log.debug("Validation-only mode disabled, Applying configs.")
        return apply_customer_configs(customer_configs)
    log.debug("Validation complete.")
    return True
