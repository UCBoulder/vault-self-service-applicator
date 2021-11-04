"""Converts a list of CustomerConfigs into one list each of policies,
groups, approles, and secret paths"""
from . import config
from .parse import Group, AppRole, PolicyRule, Capability

# pylint: disable=too-few-public-methods
class UnverifiedPolicyRule(PolicyRule):
    """Initializes PolicyRule object with no verification."""

    # pylint: disable=super-init-not-called
    def __init__(self, path, capabilities):
        self.path = path
        self.capabilities = [Capability(cap) for cap in capabilities]


def apply_group_accessors(customer_configs):
    """Creates group policy to allow specified groups to access approles."""
    for customer_conf in customer_configs:
        for approle in customer_conf.approles:
            for accessor in approle.accessor_groups:
                accessor.policies = [
                    UnverifiedPolicyRule(
                        path="auth/approle/role/{n}/role-id".format(n=approle.name),
                        capabilities=["read"],
                    ),
                    UnverifiedPolicyRule(
                        path="auth/approle/role/{n}/secret-id".format(n=approle.name),
                        capabilities=["create", "update"],
                    ),
                ]
                customer_conf.groups.append(accessor)


def flatten(customer_configs):
    """Converts a list of CustomerConfigs into one list each of policies,
    groups, approles, and secret paths"""
    targets = { Group.kind: {}, AppRole.kind: {} }
    policies = {}
    all_paths = set([])

    apply_group_accessors(customer_configs)

    for customer_conf in customer_configs:
        for target in customer_conf.groups + customer_conf.approles:

            policy_name = \
                f"{target.kind}-{target.name}" \
                if target.kind == AppRole.kind else \
                f"{target.kind}-{config.customer_prefix}-{target.name}"


            targets[target.kind][target.name] = policy_name

            if not policy_name in policies:
                policies[policy_name] = {}

            for pol in target.policies:
                all_paths.add(pol.path)

                # Intialize the path with an empty set of capabilities.
                # Use a python set to prevent duplicates.
                if not pol.path in policies[policy_name]:
                    policies[policy_name][pol.path] = set()

                # Add any new capabilities defined for the same target+path
                policies[policy_name][pol.path].update(
                    {cap.value for cap in pol.capabilities}
                )

    # keep paths that end in *, but don't contain any +
    #sanitized_paths = { p for p in all_paths if (not '+' in p and p[-1] == '*') }

    return {
        "groups": targets[Group.kind],
        "approles": targets[AppRole.kind],
        "policies": policies,
        "paths": all_paths,
    }
