"""Parse, validate, and marshall customer configs.

Attempt to ensure that configs are valid and follow
conventions. Provide useful error messages with as
much context as possible to help customer fix bad
configs.
"""
import re
from enum import Enum

import yaml
from . import config, log


# Yes, I know this returns 21th if you get that far.
def prettify_number(num):
    """Convert cardinal integer into ordinal string."""
    if num == 1:
        return "1st"
    if num == 2:
        return "2nd"
    if num == 3:
        return "3rd"

    return "{}th".format(num)

class Capability(Enum):
    """Enforce which capability strings are valid."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    DENY = "deny"
    # Don't let customers grant sudo permissions
    #SUDO = "sudo"

# pylint: disable=too-few-public-methods
class PolicyRule():
    """Represent combination of path with capabilities to be granted."""
    ALLOWED_PATH_SECTIONS = [
        # a single + character
        re.compile(r'^\+$'),
        # or at least one of a-z, A-Z, 0-9, _ or -
        re.compile(r'^[\w\-]+$'),
    ]
    NEVER_ALLOWED_ROOTS = [
        '+',
        'sys',
        'auth',
    ]

    def __init__(self, path, capabilities=None):
        # * is allowed, but only as the last character, per
        # https://www.vaultproject.io/docs/concepts/policies.html#policy-syntax
        # Rather than make special regex logic for last section, simply remove
        # trailing *, if it exists, before validating sections
        path_to_verify = path
        if path[-1] == '*':
            # Don't create trailing slash if path ends with /*
            if path_to_verify[-2] == '/':
                path_to_verify = path[:-2]
            else:
                path_to_verify = path[:-1]

        sections = path_to_verify.split('/')
        if sections[0] in self.__class__.NEVER_ALLOWED_ROOTS:
            raise ValueError("Illegal root '{s}' in path '{p}'".format(
                s = sections[0],
                p = path,
            ))
        if sections[0] != config.customer_prefix:
            explanation = "All policy paths must be children of '{c}'.".format(
                c = config.customer_prefix,
            )
            raise ValueError("{e}\nIllegal root '{s}' in path '{p}'".format(
                e = explanation,
                s = sections[0],
                p = path,
            ))
        for section in sections:
            matches = [
                bool(pattern.match(section)) for pattern in self.__class__.ALLOWED_PATH_SECTIONS
            ]
            if not any(matches):
                explanation = \
                    "Policy path sections may be a single +, or combination of a-zA-Z0-9'_''-'."
                if '*' in section:
                    explanation = "'*' is only allowed as the last character in policy path."
                if section == '':
                    explanation = \
                        "Please avoid leading `/foo`, trailing `foo/`," \
                        + "or double `foo//bar` slashes in policy path."
                raise ValueError("{e}\nInvalid section '{s}' in path '{p}'".format(
                    e = explanation,
                    s = section,
                    p = path,
                ))

        self.path = path
        if capabilities is None:
            raise ValueError("Policy path '{p}' does not have any capabilities.".format(
                p = path,
            ))
        self.capabilities = [Capability(cap) for cap in capabilities]

# pylint: disable=too-few-public-methods
class PolicyTarget():
    """Represent entity to which a policy can be applied, and its policies."""
    ALLOWED_NAME_PATTERN = None
    INVALID_NAME_EXPLANATION = None
    kind = None

    # Empty policy list allowed to revoke existing permissions
    # pylint: disable=dangerous-default-value
    def __init__(self, name=None, policies=[]):
        if not name:
            raise ValueError("Name required for {k}".format(k=self.__class__.kind))

        if not self.__class__.ALLOWED_NAME_PATTERN.match(name):
            raise ValueError("{exp}\nInvalid {k} name '{n}'".format(
                exp = self.__class__.INVALID_NAME_EXPLANATION,
                k = self.__class__.kind,
                n = name
            ))

        self.name = name
        self.policies = []
        for i, pol in enumerate(policies):
            try:
                self.policies.append(PolicyRule(**pol))
            except ValueError as err:
                raise ValueError("Error in {n} policy:\n{e}".format(
                    n = prettify_number(i + 1),
                    e = err,
                )) from err


# pylint: disable=too-few-public-methods
class Group(PolicyTarget):
    """Represent LDAP group."""
    # At least one of a-z, A-Z, 0-9, _, space, or -
    ALLOWED_NAME_PATTERN = re.compile(r'^[ ]*[\w\-]+[\w\- ]*$')
    INVALID_NAME_EXPLANATION = "Group names must only contain a-z, A-Z, 0-9, _, space, or -."
    kind = "group"

    # Empty policy list allowed to revoke existing permissions
    # pylint: disable=dangerous-default-value
    def __init__(self, name=None, policies=[]):
        PolicyTarget.__init__(self, name, policies)

        if len(config.invalid_group_prefix) > 0:
            if name.lower().startswith(config.invalid_group_prefix.lower()):
                raise ValueError("Group name must not start with '{pre}': {n}".format(
                    pre = config.invalid_group_prefix,
                    n = name,
                ))


# pylint: disable=too-few-public-methods
class AppRole(PolicyTarget):
    """Represent approle."""
    # At least one of a-z, A-Z, 0-9, _ or -
    ALLOWED_NAME_PATTERN = re.compile(r'^[\w\-]+$')
    INVALID_NAME_EXPLANATION = "Approle names must only contain a-z, A-Z, 0-9, _, or -."
    kind = "approle"

    # Empty policy list allowed to revoke existing permissions
    # pylint: disable=dangerous-default-value
    def __init__(self, name=None, policies=[], accessor_groups=[]):
        PolicyTarget.__init__(self, name, policies)

        self.accessor_groups = [Group(name=g) for g in accessor_groups]

        prefix = f"{config.customer_prefix}-"
        if not name.startswith(prefix):
            raise ValueError("Approle name must start with '{pre}': {n}".format(
                pre = prefix,
                n = name,
            ))


# pylint: disable=too-few-public-methods
class CustomerConfig():
    """Represent partial or complete customer-defined configuration."""
    # Neither group nor approle array is required
    # pylint: disable=dangerous-default-value
    def __init__(self, groups=[], approles=[]):
        self.groups = []
        for i, grp in enumerate(groups):
            try:
                self.groups.append(Group(**grp))
                log.debug(f"Found group {self.groups[-1].name}")
            except ValueError as err:
                raise ValueError("group '{g}':\n{e}".format(
                    g = grp["name"] if "name" in grp else str(i + 1),
                    e = err,
                )) from err
        self.approles = []
        for i, apr in enumerate(approles):
            try:
                self.approles.append(AppRole(**apr))
                log.debug(f"Found approle {self.approles[-1].name}")
            except ValueError as err:
                msg = ""
                if "name" in apr:
                    msg = "approle '{a}':\n".format(a = apr["name"])
                else:
                    msg = "{a} approle:\n".format(a = prettify_number(i + 1))
                raise ValueError(msg + str(err)) from err


def parse_file(path):
    """Parse single .yml file into a CustomerConfig object."""
    with open(path, 'r') as handle:
        _customer_config = yaml.safe_load(handle)
        try:
            customer_config = CustomerConfig(**_customer_config)
            log.log("{f} is valid.".format(
                f=path.split("/")[-1]
            ))
            return customer_config
        except ValueError as err:
            raise ValueError("Error parsing '{f}', in {e}".format(
                f=path,
                e=err,
            )) from err
