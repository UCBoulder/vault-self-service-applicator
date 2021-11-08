"""Connect to a Hashicorp Vault server and apply group/approle/policy configurations."""
import hvac

from . import config, log

non_kv_roots = [
    "auth",
    "sys"
]

def _success(res):
    return res.status_code >= 200 and res.status_code <= 299

def _create_or_update_group(client, name, policy_name):
    res = client.auth.ldap.create_or_update_group(
        name = name,
        policies = [ policy_name ],
    )
    log.debug(name, res)
    if not _success(res):
        log.critical(f"Failed to apply group {name}")
        log.critical(res)
        log.critical(res.headers)
        log.critical(res.text)
        return False
    return True

def _create_or_update_approle(client, name, policy_name):
    res = client.write(
        path = f"auth/approle/role/{name}",
        policies = [ policy_name ],
    )
    log.debug(name, res)
    if not _success(res):
        log.critical(f"Failed to apply approle {name}")
        log.critical(res)
        log.critical(res.headers)
        log.critical(res.text)
        return False
    return True

def _create_or_update_policy(client, name, policy):
    res = client.sys.create_or_update_policy(
        name = name,
        # This dumpster fire of an object format is still better than templating hcl. The exact
        # format is found by running: policy = client.get_policy('mypolicy', parse=True)
        #
        # The policy object should look like:
        #
        #    { 'path': {
        #        'foobar/*': { 'capabilities': ['read', 'list'] },
        #        'foobaz/*': { 'capabilities': ['read', 'list', 'update'] },
        #    }}
        #
        # Sort capabilities to enable mock testing.
        #
        policy = {
            "path": { p: { "capabilities": sorted(c)} for p, c in policy.items() }
        }
    )
    log.debug(name, res)
    if not _success(res):
        log.critical(f"Failed to apply policy {name}")
        log.critical(res)
        log.critical(res.headers)
        log.critical(res.text)
        return False
    return True

def _create_path_placeholder(client, path):
    log.log("Path placeholders not implemented yet")
    log.log(client, path)

def _mangle_kv_v2_policy(policies):
    """Apply reasonable set of transformations, per the
       strange behavior here: https://www.vaultproject.io/docs/secrets/kv/kv-v2#acl-rules"""
    # Convert capability on the base path (what you would put in a GET request), to a set of
    # capabilities on special sub-paths, like this
    #
    #        read @ customer/foo/*  -->
    #
    #        read @ customer/data/foo/*
    #     +  read @ customer/metadata/foo/*
    #
    capability_prefix_map = {
        'create': [
            { 'prefix': 'data',     'capability': 'create' },
        ],
        'read': [
            { 'prefix': 'data',     'capability': 'read' },
        ],
        'update': [
            { 'prefix': 'data',     'capability': 'update' },
        ],
        'delete': [
            { 'prefix': 'data',     'capability': 'delete' },
            { 'prefix': 'delete',   'capability': 'update' },
            { 'prefix': 'destroy',  'capability': 'update' },
            { 'prefix': 'undelete', 'capability': 'update' },
            { 'prefix': 'metadata', 'capability': 'delete' },
        ],
        'list': [
            { 'prefix': 'metadata', 'capability': 'list' },
            { 'prefix': 'metadata', 'capability': 'read' },
        ],
        'deny': [
            { 'prefix': 'data',     'capability': 'deny' },
        ],
    }
    new_policies = {}
    for path, capabilities in policies.items():
        path_sections = path.split('/')

        # Don't mangle system (non kv) paths
        if path_sections[0] in non_kv_roots:
            new_policies[path] = capabilities
        else:
            for cap in capabilities:
                for pol in capability_prefix_map[cap]:

                    # customer/foo/* -> customer/prefix/foo/*
                    new_path = path_sections.copy()
                    new_path.insert(1, pol['prefix'])
                    new_path = '/'.join(new_path)

                    if new_path not in new_policies:
                        new_policies[new_path] = set()

                    new_policies[new_path].add(
                        pol['capability']
                    )
    return new_policies

# pylint: disable=unused-argument,fixme
# todo: implement path placeholding
def apply_flat_config(groups, approles, policies, paths):
    """Loop through flattened configuration and apply it to a running server."""
    client = hvac.Client(config.vault_addr)

    client.token = config.vault_token
    if not client.is_authenticated():
        client.auth_approle(config.vault_role_id, config.vault_role_secret)

    log.debug("Authenticated with vault server {s}".format(
        s=config.vault_addr
    ))

    success = True

    for name, policy in groups.items():
        log.debug(f"Applying group {name}")
        if not _create_or_update_group(client, name, policy):
            success = False

    for name, policy in approles.items():
        log.debug(f"Applying approle {name}")
        if not _create_or_update_approle(client, name, policy):
            success = False

    for name, policy in policies.items():
        log.debug(f"Applying policy {name}")
        if not _create_or_update_policy(client, name, _mangle_kv_v2_policy(policy)):
            success = False

    #for path in paths:
        #_create_path_placeholder(client, path)

    return success
