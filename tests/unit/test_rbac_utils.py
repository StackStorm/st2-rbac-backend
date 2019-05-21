# Copyright (C) 2019 Extreme Networks, Inc - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly
# prohibited. Proprietary and confidential. See the LICENSE file
# included with this work for details.

from __future__ import absolute_import

from oslo_config import cfg

from st2tests.base import DbTestCase
from st2tests.config import parse_args
from st2common.models.db.auth import UserDB
from st2common.models.db.rbac import UserRoleAssignmentDB

from st2common.rbac.types import SystemRole
from st2common.rbac.migrations import insert_system_roles

from st2rbac_enterprise_backend.utils import RBACUtils as rbac_utils

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
