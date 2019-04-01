# Copyright (c) Extreme Networks, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential.
# See the LICENSE file included with this work for details.

import six

from st2common.service_setup import register_service_in_service_registry
from st2common.services import coordination

from st2tests import config as tests_config


from tests.base import APIControllerWithRBACTestCase

http_client = six.moves.http_client

__all__ = [
    'ServiceRegistryControllerRBACTestCase'
]


class ServiceRegistryControllerRBACTestCase(APIControllerWithRBACTestCase):

    coordinator = None

    @classmethod
    def setUpClass(cls):
        tests_config.parse_args(coordinator_noop=True)

        super(ServiceRegistryControllerRBACTestCase, cls).setUpClass()

        cls.coordinator = coordination.get_coordinator(use_cache=False)

        # Register mock service in the service registry for testing purposes
        register_service_in_service_registry(service='mock_service',
                                             capabilities={'key1': 'value1',
                                                           'name': 'mock_service'},
                                             start_heart=True)

    @classmethod
    def tearDownClass(cls):
        super(ServiceRegistryControllerRBACTestCase, cls).tearDownClass()

        coordination.coordinator_teardown(cls.coordinator)

    def test_get_groups(self):
        # Non admin users can't access that API endpoint
        for user_db in [self.users['no_permissions'], self.users['observer']]:
            self.use_user(user_db)

            resp = self.app.get('/v1/service_registry/groups', expect_errors=True)
            expected_msg = ('Administrator access required')
            self.assertEqual(resp.status_code, http_client.FORBIDDEN)
            self.assertEqual(resp.json['faultstring'], expected_msg)

        # Admin user can access it
        user_db = self.users['admin']
        self.use_user(user_db)

        resp = self.app.get('/v1/service_registry/groups')
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(resp.json, {'groups': ['mock_service']})

    def test_get_group_members(self):
        # Non admin users can't access that API endpoint
        for user_db in [self.users['no_permissions'], self.users['observer']]:
            self.use_user(user_db)

            resp = self.app.get('/v1/service_registry/groups/mock_service/members',
                                expect_errors=True)
            expected_msg = ('Administrator access required')
            self.assertEqual(resp.status_code, http_client.FORBIDDEN)
            self.assertEqual(resp.json['faultstring'], expected_msg)

        # Admin user can access it
        user_db = self.users['admin']
        self.use_user(user_db)

        resp = self.app.get('/v1/service_registry/groups/mock_service/members')
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertTrue('members' in resp.json)
