# Copyright (C) 2020 Extreme Networks, Inc - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly
# prohibited. Proprietary and confidential. See the LICENSE file
# included with this work for details.

from __future__ import absolute_import

import mock
import eventlet
from oslo_config import cfg

from st2tests.base import CleanDbTestCase
import st2auth.handlers as handlers
from st2common.models.db.auth import UserDB
from st2common.persistence.auth import User

from st2tests.mocks.auth import DUMMY_CREDS
from st2tests.mocks.auth import get_mock_backend

from st2rbac_enterprise_backend.syncer import RBACRemoteGroupToRoleSyncer
from st2rbac_enterprise_backend.service import RBACService as rbac_service

__all__ = [
    'AuthHandlerRBACRoleSyncTestCase'
]


@mock.patch('st2auth.handlers.get_auth_backend_instance', get_mock_backend)
class AuthHandlerRBACRoleSyncTestCase(CleanDbTestCase):
    def setUp(self):
        super(AuthHandlerRBACRoleSyncTestCase, self).setUp()

        cfg.CONF.set_override(group='auth', name='backend', override='mock')
        cfg.CONF.set_override(group='rbac', name='backend', override='enterprise')

        self.users = {}
        self.roles = {}
        self.role_assignments = {}

        # Insert some mock users
        user_1_db = UserDB(name='auser')
        user_1_db = User.add_or_update(user_1_db)
        self.users['user_1'] = user_1_db

        user_2_db = UserDB(name='buser')
        user_2_db = User.add_or_update(user_2_db)
        self.users['user_2'] = user_2_db

        # Insert mock local role assignments
        role_db = rbac_service.create_role(name='mock_local_role_1')
        user_db = self.users['user_1']
        source = 'assignments/%s.yaml' % user_db.name
        role_assignment_db_1 = rbac_service.assign_role_to_user(
            role_db=role_db, user_db=user_db, source=source, is_remote=False)

        self.roles['mock_local_role_1'] = role_db
        self.role_assignments['assignment_1'] = role_assignment_db_1

        role_db = rbac_service.create_role(name='mock_local_role_2')
        user_db = self.users['user_1']
        source = 'assignments/%s.yaml' % user_db.name
        role_assignment_db_2 = rbac_service.assign_role_to_user(
            role_db=role_db, user_db=user_db, source=source, is_remote=False)

        self.roles['mock_local_role_2'] = role_db
        self.role_assignments['assignment_2'] = role_assignment_db_2

        role_db = rbac_service.create_role(name='mock_role_3')
        self.roles['mock_role_3'] = role_db

        role_db = rbac_service.create_role(name='mock_role_4')
        self.roles['mock_role_4'] = role_db

        role_db = rbac_service.create_role(name='mock_role_5')
        self.roles['mock_role_5'] = role_db

    def test_group_to_role_sync_is_performed_on_successful_auth_no_groups_returned(self):
        # Enable group sync
        cfg.CONF.set_override(group='rbac', name='sync_remote_groups', override=True)

        user_db = self.users['user_1']
        h = handlers.StandaloneAuthHandler()
        request = {}

        # Verify initial state
        role_dbs = rbac_service.get_roles_for_user(user_db=user_db, include_remote=True)
        self.assertEqual(len(role_dbs), 2)
        self.assertEqual(role_dbs[0], self.roles['mock_local_role_1'])
        self.assertEqual(role_dbs[1], self.roles['mock_local_role_2'])

        # No groups configured should return early
        h._auth_backend.groups = []

        token = h.handle_auth(request, headers={}, remote_addr=None, remote_user=None,
                              authorization=('basic', DUMMY_CREDS))
        self.assertEqual(token.user, 'auser')

        # Verify nothing has changed
        role_dbs = rbac_service.get_roles_for_user(user_db=user_db, include_remote=True)
        self.assertEqual(len(role_dbs), 2)
        self.assertEqual(role_dbs[0], self.roles['mock_local_role_1'])
        self.assertEqual(role_dbs[1], self.roles['mock_local_role_2'])

    def test_group_to_role_sync_is_performed_on_successful_auth_single_group_no_mappings(self):
        # Enable group sync
        cfg.CONF.set_override(group='rbac', name='sync_remote_groups', override=True)

        user_db = self.users['user_1']
        h = handlers.StandaloneAuthHandler()
        request = {}

        # Verify initial state
        role_dbs = rbac_service.get_roles_for_user(user_db=user_db, include_remote=True)
        self.assertEqual(len(role_dbs), 2)
        self.assertEqual(role_dbs[0], self.roles['mock_local_role_1'])
        self.assertEqual(role_dbs[1], self.roles['mock_local_role_2'])

        # Single group configured but no group mapping in the database
        h._auth_backend.groups = [
            'CN=stormers,OU=groups,DC=stackstorm,DC=net'
        ]

        token = h.handle_auth(request, headers={}, remote_addr=None, remote_user=None,
                              authorization=('basic', DUMMY_CREDS))
        self.assertEqual(token.user, 'auser')

        # Verify nothing has changed
        role_dbs = rbac_service.get_roles_for_user(user_db=user_db, include_remote=True)
        self.assertEqual(len(role_dbs), 2)
        self.assertEqual(role_dbs[0], self.roles['mock_local_role_1'])
        self.assertEqual(role_dbs[1], self.roles['mock_local_role_2'])

    def test_group_to_role_sync_is_performed_on_successful_auth_with_groups_and_mappings(self):
        # Enable group sync
        cfg.CONF.set_override(group='rbac', name='sync_remote_groups', override=True)

        user_db = self.users['user_1']
        h = handlers.StandaloneAuthHandler()
        request = {}

        # Single mapping, new remote assignment should be created
        rbac_service.create_group_to_role_map(group='CN=stormers,OU=groups,DC=stackstorm,DC=net',
                                              roles=['mock_role_3', 'mock_role_4'],
                                              source='mappings/stormers.yaml')

        # Verify initial state
        role_dbs = rbac_service.get_roles_for_user(user_db=user_db, include_remote=True)
        self.assertEqual(len(role_dbs), 2)
        self.assertEqual(role_dbs[0], self.roles['mock_local_role_1'])
        self.assertEqual(role_dbs[1], self.roles['mock_local_role_2'])

        h._auth_backend.groups = [
            'CN=stormers,OU=groups,DC=stackstorm,DC=net'
        ]

        token = h.handle_auth(request, headers={}, remote_addr=None, remote_user=None,
                              authorization=('basic', DUMMY_CREDS))
        self.assertEqual(token.user, 'auser')

        # Verify a new role assignments based on the group mapping has been created
        role_dbs = rbac_service.get_roles_for_user(user_db=user_db, include_remote=True)

        self.assertEqual(len(role_dbs), 4)
        self.assertEqual(role_dbs[0], self.roles['mock_local_role_1'])
        self.assertEqual(role_dbs[1], self.roles['mock_local_role_2'])
        self.assertEqual(role_dbs[2], self.roles['mock_role_3'])
        self.assertEqual(role_dbs[3], self.roles['mock_role_4'])

    def test_group_to_role_sync_concurrent_auth(self):
        # Verify that there is no race and group sync during concurrent auth works fine
        # Enable group sync
        cfg.CONF.set_override(group='rbac', name='sync_remote_groups', override=True)

        h = handlers.StandaloneAuthHandler()
        request = {}

        def handle_auth():
            token = h.handle_auth(request, headers={}, remote_addr=None, remote_user=None,
                                  authorization=('basic', DUMMY_CREDS))
            self.assertEqual(token.user, 'auser')

        thread_pool = eventlet.GreenPool(20)

        for i in range(0, 20):
            thread_pool.spawn(handle_auth)

        thread_pool.waitall()

    @mock.patch.object(RBACRemoteGroupToRoleSyncer, 'sync',
                       mock.Mock(side_effect=Exception('throw')))
    def test_group_to_role_sync_error_non_fatal_on_succesful_auth(self):
        # Enable group sync
        cfg.CONF.set_override(group='rbac', name='sync_remote_groups', override=True)

        h = handlers.StandaloneAuthHandler()
        request = {}

        h._auth_backend.groups = [
            'CN=stormers,OU=groups,DC=stackstorm,DC=net'
        ]

        # sync() method called upon successful authentication throwing should not be fatal
        token = h.handle_auth(request, headers={}, remote_addr=None, remote_user=None,
                              authorization=('basic', DUMMY_CREDS))
        self.assertEqual(token.user, 'auser')
