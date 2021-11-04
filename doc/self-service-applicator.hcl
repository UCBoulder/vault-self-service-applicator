# Grant this policy to the user/approle that will be running this program.

path "sys/policy/*" {
    capabilities = ["create", "read", "update", "delete", "list"]
}

path "sys/policies/*" {
    capabilities = ["create", "read", "update", "delete", "list"]
}

path "auth/ldap/groups/*" {
    capabilities = ["create", "read", "update", "delete", "list"]
}

path "auth/approle/role/*" {
    capabilities = ["create", "read", "update", "delete", "list"]
}