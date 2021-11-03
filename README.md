# Vault Self-Service Applicator

For Vault administrators that cannot use the Vault Enterprise "namespaces"
feature, this python program (shipped as a container image) allows "customers"
to manage their own policies and approles.

Currently it makes several assumptions, but PRs to support other environments
are welcome:

1. Your customers each have their own kv-v2 secrets engine.
2. Access to these engines is controlled by LDAP groups.
3. The LDAP auth engine is mounted at `auth/ldap`.

## Admin usage

You will need to collect the desired configuration from each customer (probably
with a git repo), then for each customer run the following:

    export VAULT_TOKEN="s.YOUR_VAULT_TOKEN"

    export CUSTOMER_CONFIG_DIR="./configs/customer"
    export CUSTOMER_PREFIX="customer-secret-engine"
    python entrypoint.py

## Contributing

If you wish to make software changes, please consider submitting them with a PR.
You may build the container locally as follows:

    docker build -t vault-self-service-applicator:new-feature .

This will also perform linting, and run unit tests. No image will be produced if
either fails.

## Customer configuration format

Customers may check the validity their configuration by running:

    export ONLY_VALIDATE="True"
    export CUSTOMER_CONFIG_DIR="./my-configs"
    export CUSTOMER_PREFIX="my-secret-engine"
    python entrypoint.py

### YAML files

You may create as many `.yml` files as you would like. The applied configuration
will be the same whether you choose to define one big file or split it up by
project.

Each file may specify up to one list of groups and up to one list of approles.
Like so:

    groups:
      - name: customer-ops
        policies:
          - path: 'example/foo/*'
        capabilities: ['create', 'read', 'update', 'delete', 'list']
      - name: customer-dev
        policies:
          - path: 'example/dev/*'
            capabilities: ['create', 'read', 'update', 'delete', 'list']

or

    approles:
      - name: example-foo-prod
        policies:
          - path: 'example/foo/prod'
            capabilities: ['read']
        accessor_groups:
          - customer-ops

or combined, like:

    groups:
      - name: customer-ops
        policies:
          - path: 'example/foo/*'
            capabilities: ['create', 'read', 'update', 'delete', 'list']
    approles:
      - name: example-foo-prod
        policies:
          - path: 'example/foo/prod'
            capabilities: ['read']
        accessor_groups:
          - customer-ops

### Groups

In order to be useful, group names must correspond exactly to an LDAP group.
Once applied, members of that group will have the specified capabilities in
Vault.

### Approles

Approle names must start with your prefix. They will be created if they do not
already exist, otherwise their capabilities will be updated.

Members of any groups listed under `accessor_groups` will be able to access
the role-id and generate the secret-id necessary for authenticating wth the
approle, per this [doc](https://learn.hashicorp.com/tutorials/vault/approle#step-3-get-roleid-and-secretid).

### Paths

All paths must start with your prefix (the name of your kv-v2 engine). This
prevents you from accidentally modifying anyone else's configuration.

### Capabilities

Valid capabilities are: ["create", "read", "update", "delete", "list", "deny"].
You can get more info [here](https://www.vaultproject.io/docs/concepts/policies.html#capabilities).
The "deny" capability will cancel out any others that may be granted.

### Merging

If the same group or approle is specified in multiple files, it will be granted
the union of all specified capabilities.


