from unittest import TestCase, mock
#import pytest

from self_service import translate, parse

class TestParse(TestCase):

    def setUp(self):
        self.config = mock.patch('self_service.translate.config',
            customer_prefix='foo',
        )
        self.config2 = mock.patch('self_service.parse.config',
            customer_prefix='foo',
        )
        self.config.start()
        self.config2.start()

    def tearDown(self):
        self.config.stop()
        self.config2.stop()

    # pylint: disable=no-self-use
    def test_simple_case(self):
        customer_config_1 = parse.CustomerConfig(
            groups=[
                {"name": "Group-1", "policies": [
                    {"path": "foo/bar", "capabilities": ['read', 'list']},
                ]},
                {"name": "Group-2", "policies": [
                    {"path": "foo/baz", "capabilities": ['read', 'list']},
                ]},
            ],
        )
        customer_config_2 = parse.CustomerConfig(
            groups=[
                {"name": "Group-1", "policies": [
                    {"path": "foo/bar", "capabilities": ['list', 'create', 'update']},
                ]},
            ],
            approles=[
                {
                    "name": "foo-Approle-1",
                    "policies": [
                      {"path": "foo/bar", "capabilities": ['read', 'list']},
                    ],
                    "accessor_groups": [
                        "Group-1", "Group-3"
                    ]
                },
            ],
        )
        ret = translate.flatten([customer_config_1, customer_config_2])
        assert ret["groups"]["Group-1"] == "group-foo-Group-1"
        assert ret["policies"]["group-foo-Group-1"] == {
            "foo/bar": {"read", "list", "create", "update"},
            "auth/approle/role/foo-Approle-1/role-id": {"read"},
            "auth/approle/role/foo-Approle-1/secret-id": {"create", "update"},
        }
        assert ret["approles"]["foo-Approle-1"] == "approle-foo-Approle-1"
        assert ret["policies"]["approle-foo-Approle-1"] == {
            "foo/bar": {"read", "list"}
        }
        assert ret["groups"]["Group-2"] == "group-foo-Group-2"
        assert ret["policies"]["group-foo-Group-2"] == {
            "foo/baz": {"read", "list"}
        }
        assert ret["policies"]["group-foo-Group-3"] == {
            "auth/approle/role/foo-Approle-1/role-id": {"read"},
            "auth/approle/role/foo-Approle-1/secret-id": {"create", "update"},
        }
