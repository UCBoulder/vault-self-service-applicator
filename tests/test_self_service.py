
from unittest import TestCase, mock
#import pytest

from self_service import self_service

class TestApply(TestCase):

    def setUp(self):
        self.config = [
            mock.patch("self_service.config.customer_config_dir",
                "tests/examples/customer_dir",
            ),
            mock.patch("self_service.parse.config",
                customer_prefix="customer",
            ),
            mock.patch("self_service.hashivault.config",
                customer_prefix="customer",
                vault_addr="mock_vault_addr",
                vault_role_id="mock_vault_role_id",
                vault_role_secret="mock_role_secret",
            ),
            mock.patch("self_service.translate.config",
                customer_prefix="customer",
            ),
            mock.patch("self_service.config.only_validate",
                False,
            ),
        ]
        for ptch in self.config:
            ptch.start()
        self.hvac_client = mock.Mock()
        self.hvac_client.is_authenticated.return_value = False
        self.hvac_client.auth.ldap.create_or_update_group.return_value = mock.Mock(status_code=204)
        self.hvac_client.write.return_value = mock.Mock(status_code=204)
        self.hvac_client.sys.create_or_update_policy.return_value = mock.Mock(status_code=204)
        self.hvac_patch = mock.patch("self_service.hashivault.hvac")
        self.hvac = self.hvac_patch.start()
        self.hvac.Client.return_value = self.hvac_client

    def tearDown(self):
        for ptch in self.config:
            ptch.stop()
        self.hvac_patch.stop()

    # pylint: disable=no-self-use
    def test_full_stack(self):
        self_service.main()
        self.hvac.Client.assert_has_calls(
            [mock.call("mock_vault_addr")],
            any_order=True,
        )
        self.hvac_client.auth_approle.assert_has_calls(
            [mock.call("mock_vault_role_id", "mock_role_secret")],
            any_order=True,
        )
        self.hvac_client.auth.ldap.create_or_update_group.assert_has_calls([
            mock.call(name="customer-ops",
                policies=["group-customer-customer-ops"]),
            mock.call(name="customer-foo-dev",
                policies=["group-customer-customer-foo-dev"]),
            mock.call(name="customer-bar-dev",
                policies=["group-customer-customer-bar-dev"]),
        ], any_order=True)

        self.hvac_client.write.assert_has_calls([
            mock.call(path="auth/approle/role/customer-foo-prod",
                policies=["approle-customer-foo-prod"]),
            mock.call(path="auth/approle/role/customer-bar-prod",
                policies=["approle-customer-bar-prod"]),
        ], any_order=True)

        self.hvac_client.sys.create_or_update_policy.assert_has_calls([
            mock.call(name="group-customer-customer-ops",
                policy={"path": {
                    "customer/data/foo/*":     {"capabilities":
                        ["create", "delete", "read", "update"]
                    },
                    "customer/metadata/foo/*": {"capabilities":
                        ["delete", "list", "read"]
                    },
                    "customer/delete/foo/*":   {"capabilities": ["update"]},
                    "customer/destroy/foo/*":  {"capabilities": ["update"]},
                    "customer/undelete/foo/*": {"capabilities": ["update"]},
                    "customer/data/bar/*":     {"capabilities":
                        ["create", "delete", "read", "update"]
                    },
                    "customer/metadata/bar/*": {"capabilities":
                        ["delete", "list", "read"]
                    },
                    "customer/delete/bar/*":   {"capabilities": ["update"]},
                    "customer/destroy/bar/*":  {"capabilities": ["update"]},
                    "customer/undelete/bar/*": {"capabilities": ["update"]},
                }}),
            mock.call(name="group-customer-customer-foo-dev",
                policy={"path": {
                    "customer/data/foo/dev":     {"capabilities":
                        ["create", "read", "update"]
                    },
                    "customer/metadata/foo/dev": {"capabilities":
                        ["list", "read"]
                    },
                }}),
            mock.call(name="group-customer-customer-bar-dev",
                policy={"path": {
                    "customer/data/bar/dev":     {"capabilities":
                        ["create", "read", "update"]
                    },
                    "customer/metadata/bar/dev": {"capabilities":
                        ["list", "read"]
                    },
                }}),
            mock.call(name="approle-customer-foo-prod",
                policy={"path": {
                    "customer/data/foo/prod":     {"capabilities":
                        ["read"]
                    },
                }}),
            mock.call(name="approle-customer-bar-prod",
                policy={"path": {
                    "customer/data/bar/prod":     {"capabilities":
                        ["read"]
                    },
                }}),
        ], any_order=True)
