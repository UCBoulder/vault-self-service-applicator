from unittest import TestCase, mock
#import pytest

from self_service import hashivault

class TestApply(TestCase):

    def setUp(self):
        self.config = mock.patch('self_service.parse.config',
            customer_prefix='customer',
        )
        self.config.start()

    def tearDown(self):
        self.config.stop()

    # pylint: disable=no-self-use
    def test_mangle(self):
        in_policy = {
            'customer/app/prod/*': [ 'create', 'read', 'update', 'delete', 'list' ],
            'customer/app/dev/*': [ 'deny' ],
            'auth/approle/role/foo-Approle-1/role-id': [ 'read' ],
            'auth/approle/role/foo-Approle-1/secret-id': [ 'create', 'update' ],
        }
        # pylint: disable=protected-access
        out_policy = hashivault._mangle_kv_v2_policy(in_policy)
        assert out_policy.keys() == {
            'customer/data/app/dev/*',
            'customer/data/app/prod/*',
            'customer/metadata/app/prod/*',
            'customer/delete/app/prod/*',
            'customer/destroy/app/prod/*',
            'customer/undelete/app/prod/*',
            'auth/approle/role/foo-Approle-1/role-id',
            'auth/approle/role/foo-Approle-1/secret-id',
        }
        assert set(out_policy['customer/data/app/dev/*']) == {'deny'}
        assert set(out_policy['customer/data/app/prod/*']) == {'create', 'read', 'update', 'delete'}
        assert set(out_policy['customer/metadata/app/prod/*']) == {'read', 'delete', 'list'}
        assert set(out_policy['customer/delete/app/prod/*']) == {'update'}
        assert set(out_policy['customer/destroy/app/prod/*']) == {'update'}
        assert set(out_policy['customer/undelete/app/prod/*']) == {'update'}
        assert set(out_policy['auth/approle/role/foo-Approle-1/role-id']) == {'read'}
        assert set(out_policy['auth/approle/role/foo-Approle-1/secret-id']) == {'create', 'update'}
