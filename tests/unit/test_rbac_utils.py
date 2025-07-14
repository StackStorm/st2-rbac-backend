# Copyright 2020 The StackStorm Authors.
# Copyright (C) 2020 Extreme Networks, Inc - All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

from oslo_config import cfg

from st2tests.base import DbTestCase
from st2tests.config import parse_args
from st2common.models.db.auth import UserDB
from st2common.models.db.rbac import UserRoleAssignmentDB

from st2common.rbac.types import SystemRole
from st2common.rbac.migrations import insert_system_roles

from st2rbac_backend.utils import RBACUtils as rbac_utils

__all__ = [
    'RBACUtilsTestCase'
]


class RBACUtilsTestCase(DbTestCase):
    @classmethod
    def setUpClass(cls):
        super(RBACUtilsTestCase, cls).setUpClass()

        # TODO: Put in the base rbac db test case
        insert_system_roles()

        # Add mock users - system admin, admin, non-admin
        cls.system_admin_user = UserDB(name='system_admin_user')
        cls.system_admin_user.save()

        cls.admin_user = UserDB(name='admin_user')
        cls.admin_user.save()

        cls.regular_user = UserDB(name='regular_user')
        cls.regular_user.save()

        # Add system admin role assignment
        role_assignment_1 = UserRoleAssignmentDB(
            user=cls.system_admin_user.name, role=SystemRole.SYSTEM_ADMIN,
            source='assignments/%s.yaml' % cls.system_admin_user.name)
        role_assignment_1.save()

        # Add admin role assignment
        role_assignment_2 = UserRoleAssignmentDB(
            user=cls.admin_user.name, role=SystemRole.ADMIN,
            source='assignments/%s.yaml' % cls.admin_user.name)
        role_assignment_2.save()

    def setUp(self):
        parse_args()

    def test_is_system_admin(self):
        # Make sure RBAC is enabled for the tests
        cfg.CONF.set_override(name='enable', override=True, group='rbac')

        # System Admin user
        self.assertTrue(rbac_utils.user_is_system_admin(user_db=self.system_admin_user))

        # Admin user
        self.assertFalse(rbac_utils.user_is_system_admin(user_db=self.admin_user))

        # Regular user
        self.assertFalse(rbac_utils.user_is_system_admin(user_db=self.regular_user))

    def test_is_admin(self):
        # Make sure RBAC is enabled for the tests
        cfg.CONF.set_override(name='enable', override=True, group='rbac')

        # Admin user
        self.assertTrue(rbac_utils.user_is_admin(user_db=self.admin_user))

        # Regular user
        self.assertFalse(rbac_utils.user_is_admin(user_db=self.regular_user))

    def test_has_role(self):
        # Make sure RBAC is enabled for the tests
        cfg.CONF.set_override(name='enable', override=True, group='rbac')

        # Admin user
        self.assertTrue(rbac_utils.user_has_role(user_db=self.admin_user, role=SystemRole.ADMIN))

        # Regular user
        self.assertFalse(rbac_utils.user_has_role(user_db=self.regular_user, role=SystemRole.ADMIN))

    def test_has_system_role(self):
        # Make sure RBAC is enabled for the tests
        cfg.CONF.set_override(name='enable', override=True, group='rbac')

        # Admin user
        self.assertTrue(rbac_utils.user_has_system_role(user_db=self.admin_user))

        # Regular user
        self.assertFalse(rbac_utils.user_has_system_role(user_db=self.regular_user))
