from unittest import TestCase, mock
import pytest

from self_service import parse

class TestParse(TestCase):

    def setUp(self):
        self.config = mock.patch("self_service.parse.config",
            customer_prefix = "customer",
            invalid_group_prefix = "bad-group",
        )
        self.config.start()

    def tearDown(self):
        self.config.stop()

    # pylint: disable=no-self-use
    def test_approle_accessors(self):
        custom_config = parse.parse_file('tests/examples/approle-accessors.yml')
        test_approle = \
            [a for a in custom_config.approles if a.name == 'customer-application-dev'][0]
        flattened_accessors = [a.name for a in test_approle.accessor_groups]
        assert len(flattened_accessors) == 2
        assert 'customer-prod-admin' in flattened_accessors
        assert 'customer-dev-admin' in flattened_accessors


    # pylint: disable=no-self-use
    def test_bad_approle_name(self):
        with pytest.raises(ValueError) as err:
            assert parse.parse_file('tests/examples/bad-approle-name.yml')
        assert "Error parsing 'tests/examples/bad-approle-name.yml'" in str(err.value)
        assert "in approle 'customer-But spaces are not'" in str(err.value)
        assert "Invalid approle name 'customer-But spaces are not'" in str(err.value)

    # pylint: disable=no-self-use
    def test_bad_capability(self):
        with pytest.raises(ValueError) as err:
            assert parse.parse_file('tests/examples/bad-capability.yml')
        assert "Error parsing 'tests/examples/bad-capability.yml'" in str(err.value)
        assert "in group 'customer-prod-admin'" in str(err.value)
        assert "'foobar' is not a valid Capability" in str(err.value)

    # pylint: disable=no-self-use
    def test_bad_group_name(self):
        with pytest.raises(ValueError) as err:
            assert parse.parse_file('tests/examples/bad-group-name.yml')
        assert "Error parsing 'tests/examples/bad-group-name.yml'" in str(err.value)
        assert "in group 'But, commas are not'" in str(err.value)
        assert "Invalid group name 'But, commas are not'" in str(err.value)

    # pylint: disable=no-self-use
    def test_bad_group_name_prefix(self):
        with pytest.raises(ValueError) as err:
            assert parse.parse_file('tests/examples/bad-group-name-prefix.yml')
        assert "Error parsing 'tests/examples/bad-group-name-prefix.yml'" in str(err.value)
        assert "in group 'bad-GROUP-foobar'" in str(err.value)
        assert "Group name must not start with 'bad-group': bad-GROUP-foobar" in str(err.value)

    # pylint: disable=no-self-use
    def test_correct_config(self):
        custom_config = parse.parse_file('tests/examples/correct.yml')
        test_group = \
            [g for g in custom_config.groups if g.name == 'customer-prod-reader'][0]
        test_pol = test_group.policies[0]
        assert test_pol.path == 'customer/prod/*'
        assert test_pol.capabilities == [
            parse.Capability.READ,
            parse.Capability.LIST,
        ]

    # pylint: disable=no-self-use
    def test_illegal_approle_name(self):
        with pytest.raises(ValueError) as err:
            assert parse.parse_file('tests/examples/illegal-approle-name.yml')
        assert "Error parsing 'tests/examples/illegal-approle-name.yml'" in str(err.value)
        assert "in approle 'application-prod'" in str(err.value)
        assert "Approle name must start with 'customer-'" in str(err.value)

    # pylint: disable=no-self-use
    def test_illegal_approle_path(self):
        with pytest.raises(ValueError) as err:
            assert parse.parse_file('tests/examples/illegal-approle-path.yml')
        assert "Error parsing 'tests/examples/illegal-approle-path.yml'" in str(err.value)
        assert "in approle 'customer-application-prod'" in str(err.value)
        assert "Error in 1st policy" in str(err.value)
        assert "All policy paths must be children of 'customer'" in str(err.value)
        assert "Illegal root 'customer_other' in path 'customer_other/prod/application/*'"\
            in str(err.value)

    # pylint: disable=no-self-use
    def test_illegal_group_path(self):
        with pytest.raises(ValueError) as err:
            assert parse.parse_file('tests/examples/illegal-group-path.yml')
        assert "Error parsing 'tests/examples/illegal-group-path.yml'" in str(err.value)
        assert "in group 'customer-prod-admin" in str(err.value)
        assert "Error in 1st policy" in str(err.value)
        assert "All policy paths must be children of 'customer'" in str(err.value)
        assert "Illegal root 'other_customer' in path 'other_customer/prod/*'" in str(err.value)

    # pylint: disable=no-self-use
    def test_never_allowed_path(self):
        with pytest.raises(ValueError) as err:
            assert parse.parse_file('tests/examples/never-allowed-path.yml')
        assert "Error parsing 'tests/examples/never-allowed-path.yml'" in str(err.value)
        assert "in group 'customer-prod-admin'" in str(err.value)
        assert "Error in 1st policy" in str(err.value)
        assert "Illegal root 'sys' in path 'sys/foobar/*'" in str(err.value)

    # pylint: disable=no-self-use
    def test_no_capabilities(self):
        with pytest.raises(ValueError) as err:
            assert parse.parse_file('tests/examples/no-capabilities.yml')
        assert "Error parsing 'tests/examples/no-capabilities.yml'" in str(err.value)
        assert "in group 'customer-prod-admin" in str(err.value)
        assert "'customer/prod/*' does not have any capabilities" in str(err.value)
