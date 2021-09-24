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

from st2common.constants.keyvalue import FULL_SYSTEM_SCOPE, FULL_USER_SCOPE
from st2common.rbac.types import PermissionType
from st2common.rbac.types import ResourceType
from st2common.persistence.auth import User
from st2common.persistence.rbac import Role
from st2common.persistence.rbac import UserRoleAssignment
from st2common.persistence.rbac import PermissionGrant
from st2common.persistence.keyvalue import KeyValuePair
from st2common.models.db.keyvalue import KeyValuePairDB
from st2common.models.db.auth import UserDB
from st2common.models.db.rbac import RoleDB
from st2common.models.db.rbac import UserRoleAssignmentDB
from st2common.models.db.rbac import PermissionGrantDB
from st2common.services.keyvalues import get_key_reference

from st2rbac_backend.resolvers import KeyValuePermissionsResolver
from tests.unit.test_rbac_resolvers import BasePermissionsResolverTestCase

__all__ = [
    "KeyValuePermissionsResolverTestCase",
    "KeyValueSystemScopePermissionsResolverTestCase",
    "KeyValueUserScopePermissionsResolverTestCase",
]


class KeyValuePermissionsResolverTestCase(BasePermissionsResolverTestCase):
    @classmethod
    def setUpClass(cls):
        super(KeyValuePermissionsResolverTestCase, cls).setUpClass()

        cls.all_permission_types = PermissionType.get_valid_permissions_for_resource_type(
            ResourceType.KEY_VALUE_PAIR
        )

        cls.read_permission_types = [
            PermissionType.KEY_VALUE_PAIR_LIST,
            PermissionType.KEY_VALUE_PAIR_VIEW,
        ]

        cls.write_permission_types = [
            PermissionType.KEY_VALUE_PAIR_SET,
            PermissionType.KEY_VALUE_PAIR_DELETE,
        ]


class KeyValueSystemScopePermissionsResolverTestCase(KeyValuePermissionsResolverTestCase):
    def setUp(self):
        super(KeyValueSystemScopePermissionsResolverTestCase, self).setUp()

        # Insert system scoped key value pairs.
        kvp_1_db = KeyValuePairDB(
            uid="%s:%s:key1" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE),
            scope=FULL_SYSTEM_SCOPE,
            name="key1",
            value="val1",
        )
        kvp_1_db = KeyValuePair.add_or_update(kvp_1_db)
        self.resources[kvp_1_db.uid] = kvp_1_db

        kvp_2_db = KeyValuePairDB(
            uid="%s:%s:key2" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE),
            scope=FULL_SYSTEM_SCOPE,
            name="key2",
            value="val2",
        )
        kvp_2_db = KeyValuePair.add_or_update(kvp_2_db)
        self.resources[kvp_2_db.uid] = kvp_2_db

    def test_admin_permissions_for_system_scope_kvps(self):
        resolver = KeyValuePermissionsResolver()

        user_db = self.users["admin"]

        # Admin user should have general list permissions on system kvps.
        self.assertUserHasResourceDbPermission(
            resolver=resolver,
            user_db=user_db,
            resource_db=KeyValuePairDB(scope=FULL_SYSTEM_SCOPE),
            permission_type=PermissionType.KEY_VALUE_PAIR_LIST,
        )

        # Admin user should have all permission on the system kvps
        for k in ["key1", "key2"]:
            kvp_uid = "%s:%s:%s" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE, k)
            kvp_db = self.resources[kvp_uid]

            self.assertUserHasResourceDbPermissions(
                resolver=resolver,
                user_db=user_db,
                resource_db=kvp_db,
                permission_types=self.all_permission_types,
            )

            self.assertUserHasResourceDbPermission(
                resolver=resolver,
                user_db=user_db,
                resource_db=kvp_db,
                permission_type=PermissionType.KEY_VALUE_PAIR_ALL,
            )

    def test_observer_permissions_for_system_scope_kvps(self):
        resolver = KeyValuePermissionsResolver()

        user_db = self.users["observer"]

        # Observer user should have general list permissions on system kvps.
        self.assertUserHasResourceDbPermission(
            resolver=resolver,
            user_db=user_db,
            resource_db=KeyValuePairDB(scope=FULL_SYSTEM_SCOPE),
            permission_type=PermissionType.KEY_VALUE_PAIR_LIST,
        )

        # Observer user should have read permissions but not write permissions on the system kvps
        for k in ["key1", "key2"]:
            kvp_uid = "%s:%s:%s" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE, k)
            kvp_db = self.resources[kvp_uid]

            self.assertUserHasResourceDbPermissions(
                resolver=resolver,
                user_db=user_db,
                resource_db=kvp_db,
                permission_types=self.read_permission_types,
            )

            self.assertUserDoesntHaveResourceDbPermissions(
                resolver=resolver,
                user_db=user_db,
                resource_db=kvp_db,
                permission_types=self.write_permission_types,
            )

            self.assertUserDoesntHaveResourceDbPermission(
                resolver=resolver,
                user_db=user_db,
                resource_db=kvp_db,
                permission_type=PermissionType.KEY_VALUE_PAIR_ALL,
            )

    def test_user_default_permissions_for_system_scope_kvps(self):
        resolver = KeyValuePermissionsResolver()

        user1_db = self.users["no_roles"]
        user2_db = self.users["1_custom_role_no_permissions"]

        # Users by default should not have general list permissions on system kvps.
        self.assertUserDoesntHaveResourceDbPermission(
            resolver=resolver,
            user_db=user1_db,
            resource_db=KeyValuePairDB(scope=FULL_SYSTEM_SCOPE),
            permission_type=PermissionType.KEY_VALUE_PAIR_LIST,
        )

        self.assertUserDoesntHaveResourceDbPermission(
            resolver=resolver,
            user_db=user2_db,
            resource_db=KeyValuePairDB(scope=FULL_SYSTEM_SCOPE),
            permission_type=PermissionType.KEY_VALUE_PAIR_LIST,
        )

        for k in ["key1", "key2"]:
            kvp_uid = "%s:%s:%s" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE, k)
            kvp_db = self.resources[kvp_uid]

            # User with no roles should not have any permission on the system kvp
            self.assertUserDoesntHaveResourceDbPermissions(
                resolver=resolver,
                user_db=user1_db,
                resource_db=kvp_db,
                permission_types=self.all_permission_types,
            )

            self.assertUserDoesntHaveResourceDbPermission(
                resolver=resolver,
                user_db=user1_db,
                resource_db=kvp_db,
                permission_type=PermissionType.KEY_VALUE_PAIR_ALL,
            )

            # User with some unrelated custom roles should not have any permission on the system kvp
            self.assertUserDoesntHaveResourceDbPermissions(
                resolver=resolver,
                user_db=user2_db,
                resource_db=kvp_db,
                permission_types=self.all_permission_types,
            )

            self.assertUserDoesntHaveResourceDbPermission(
                resolver=resolver,
                user_db=user2_db,
                resource_db=kvp_db,
                permission_type=PermissionType.KEY_VALUE_PAIR_ALL,
            )

    def test_user_custom_read_permissions_for_system_scope_kvps(self):
        resolver = KeyValuePermissionsResolver()

        kvp_1_uid = "%s:%s:key1" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE)
        kvp_1_db = self.resources[kvp_1_uid]

        kvp_2_uid = "%s:%s:key2" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE)
        kvp_2_db = self.resources[kvp_2_uid]

        # Setup user, grant, role, and assignment records
        user_db = UserDB(name="system_key1_read")
        user_db = User.add_or_update(user_db)
        self.users[user_db.name] = user_db

        grant_db = PermissionGrantDB(
            resource_uid=kvp_1_db.get_uid(),
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=self.read_permission_types,
        )
        grant_db = PermissionGrant.add_or_update(grant_db)

        role_db = RoleDB(
            name="custom_role_system_key1_read_grant",
            permission_grants=[str(grant_db.id)],
        )
        role_db = Role.add_or_update(role_db)
        self.roles[role_db.name] = role_db

        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=role_db.name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        # User should not have general list permissions on system kvps.
        self.assertUserDoesntHaveResourceDbPermission(
            resolver=resolver,
            user_db=user_db,
            resource_db=KeyValuePairDB(scope=FULL_SYSTEM_SCOPE),
            permission_type=PermissionType.KEY_VALUE_PAIR_LIST,
        )

        # User should have read but no write permissions on system kvp key1.
        self.assertUserHasResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_1_db,
            permission_types=self.read_permission_types,
        )

        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_1_db,
            permission_types=self.write_permission_types,
        )

        # User should have no read and no write permissions on system kvp key2.
        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_2_db,
            permission_types=self.read_permission_types,
        )

        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_2_db,
            permission_types=self.write_permission_types,
        )

    def test_user_custom_write_permissions_for_system_scope_kvps(self):
        resolver = KeyValuePermissionsResolver()

        kvp_1_uid = "%s:%s:key1" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE)
        kvp_1_db = self.resources[kvp_1_uid]

        kvp_2_uid = "%s:%s:key2" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE)
        kvp_2_db = self.resources[kvp_2_uid]

        # Setup user, grant, role, and assignment records
        user_db = UserDB(name="system_key1_set")
        user_db = User.add_or_update(user_db)
        self.users[user_db.name] = user_db

        grant_db = PermissionGrantDB(
            resource_uid=kvp_1_db.get_uid(),
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=self.write_permission_types,
        )
        grant_db = PermissionGrant.add_or_update(grant_db)

        role_db = RoleDB(
            name="custom_role_system_key1_set_grant",
            permission_grants=[str(grant_db.id)],
        )
        role_db = Role.add_or_update(role_db)
        self.roles[role_db.name] = role_db

        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=role_db.name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        # User should not have general list permissions on system kvps.
        self.assertUserDoesntHaveResourceDbPermission(
            resolver=resolver,
            user_db=user_db,
            resource_db=KeyValuePairDB(scope=FULL_SYSTEM_SCOPE),
            permission_type=PermissionType.KEY_VALUE_PAIR_LIST,
        )

        # User should have read and write permissions on system kvp key1.
        self.assertUserHasResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_1_db,
            permission_types=self.read_permission_types,
        )

        self.assertUserHasResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_1_db,
            permission_types=self.write_permission_types,
        )

        # User should have no read and no write permissions on system kvp key2.
        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_2_db,
            permission_types=self.read_permission_types,
        )

        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_2_db,
            permission_types=self.write_permission_types,
        )

    def test_user_custom_set_permissions_for_system_scope_kvps(self):
        resolver = KeyValuePermissionsResolver()

        kvp_1_uid = "%s:%s:key1" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE)
        kvp_1_db = self.resources[kvp_1_uid]

        kvp_2_uid = "%s:%s:key2" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE)
        kvp_2_db = self.resources[kvp_2_uid]

        # Setup user, grant, role, and assignment records
        user_db = UserDB(name="system_key1_set")
        user_db = User.add_or_update(user_db)
        self.users[user_db.name] = user_db

        grant_db = PermissionGrantDB(
            resource_uid=kvp_1_db.get_uid(),
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_PAIR_SET],
        )
        grant_db = PermissionGrant.add_or_update(grant_db)

        role_db = RoleDB(
            name="custom_role_system_key1_set_grant",
            permission_grants=[str(grant_db.id)],
        )
        role_db = Role.add_or_update(role_db)
        self.roles[role_db.name] = role_db

        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=role_db.name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        # User should not have general list permissions on system kvps.
        self.assertUserDoesntHaveResourceDbPermission(
            resolver=resolver,
            user_db=user_db,
            resource_db=KeyValuePairDB(scope=FULL_SYSTEM_SCOPE),
            permission_type=PermissionType.KEY_VALUE_PAIR_LIST,
        )

        # User should have read and set but no delete permissions on system kvp key1.
        self.assertUserHasResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_1_db,
            permission_types=self.read_permission_types,
        )

        self.assertUserHasResourceDbPermission(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_1_db,
            permission_type=PermissionType.KEY_VALUE_PAIR_SET,
        )

        self.assertUserDoesntHaveResourceDbPermission(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_1_db,
            permission_type=PermissionType.KEY_VALUE_PAIR_DELETE,
        )

        # User should have no read and no write permissions on system kvp key2.
        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_2_db,
            permission_types=self.read_permission_types,
        )

        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_2_db,
            permission_types=self.write_permission_types,
        )

    def test_user_custom_delete_permissions_for_system_scope_kvps(self):
        resolver = KeyValuePermissionsResolver()

        kvp_1_uid = "%s:%s:key1" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE)
        kvp_1_db = self.resources[kvp_1_uid]

        kvp_2_uid = "%s:%s:key2" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE)
        kvp_2_db = self.resources[kvp_2_uid]

        # Setup user, grant, role, and assignment records
        user_db = UserDB(name="system_key1_delete")
        user_db = User.add_or_update(user_db)
        self.users[user_db.name] = user_db

        grant_db = PermissionGrantDB(
            resource_uid=kvp_1_db.get_uid(),
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_PAIR_DELETE],
        )
        grant_db = PermissionGrant.add_or_update(grant_db)

        role_db = RoleDB(
            name="custom_role_system_key1_delete_grant",
            permission_grants=[str(grant_db.id)],
        )
        role_db = Role.add_or_update(role_db)
        self.roles[role_db.name] = role_db

        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=role_db.name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        # User should have read and delete but no set permissions on system kvp key1.
        self.assertUserHasResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_1_db,
            permission_types=self.read_permission_types,
        )

        self.assertUserHasResourceDbPermission(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_1_db,
            permission_type=PermissionType.KEY_VALUE_PAIR_DELETE,
        )

        self.assertUserDoesntHaveResourceDbPermission(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_1_db,
            permission_type=PermissionType.KEY_VALUE_PAIR_SET,
        )

        # User should have no read and no write permissions on system kvp key2.
        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_2_db,
            permission_types=self.read_permission_types,
        )

        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_2_db,
            permission_types=self.write_permission_types,
        )

    def test_user_custom_all_permissions_for_system_scope_kvps(self):
        resolver = KeyValuePermissionsResolver()

        kvp_1_uid = "%s:%s:key1" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE)
        kvp_1_db = self.resources[kvp_1_uid]

        kvp_2_uid = "%s:%s:key2" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE)
        kvp_2_db = self.resources[kvp_2_uid]

        # Setup user, grant, role, and assignment records
        user_db = UserDB(name="system_key1_all")
        user_db = User.add_or_update(user_db)
        self.users[user_db.name] = user_db

        grant_db = PermissionGrantDB(
            resource_uid=kvp_1_db.get_uid(),
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_PAIR_ALL],
        )
        grant_db = PermissionGrant.add_or_update(grant_db)

        role_db = RoleDB(
            name="custom_role_system_key1_all_grant",
            permission_grants=[str(grant_db.id)],
        )
        role_db = Role.add_or_update(role_db)
        self.roles[role_db.name] = role_db

        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=role_db.name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        # User should not have general list permissions on system kvps.
        self.assertUserDoesntHaveResourceDbPermission(
            resolver=resolver,
            user_db=user_db,
            resource_db=KeyValuePairDB(scope=FULL_SYSTEM_SCOPE),
            permission_type=PermissionType.KEY_VALUE_PAIR_LIST,
        )

        # User should have read and write permissions on system kvp key1.
        self.assertUserHasResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_1_db,
            permission_types=self.read_permission_types,
        )

        self.assertUserHasResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_1_db,
            permission_types=self.write_permission_types,
        )

        # User should have no read and no write permissions on system kvp key2.
        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_2_db,
            permission_types=self.read_permission_types,
        )

        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=kvp_2_db,
            permission_types=self.write_permission_types,
        )


class KeyValueUserScopePermissionsResolverTestCase(KeyValuePermissionsResolverTestCase):
    def test_user_permissions_for_user_scope_kvps(self):
        resolver = KeyValuePermissionsResolver()

        # Setup users. No explicit grant, role, and assignment records should be
        # required for user to access their KVPs
        user_1_db = UserDB(name="user101")
        user_1_db = User.add_or_update(user_1_db)
        self.users[user_1_db.name] = user_1_db

        user_2_db = UserDB(name="user102")
        user_2_db = User.add_or_update(user_2_db)
        self.users[user_2_db.name] = user_2_db

        # Insert user scoped key value pairs for user1.
        key_1_name = "mykey1"
        key_1_ref = get_key_reference(FULL_USER_SCOPE, key_1_name, user_1_db.name)
        kvp_1_db = KeyValuePairDB(
            uid="%s:%s:%s" % (ResourceType.KEY_VALUE_PAIR, FULL_USER_SCOPE, key_1_ref),
            scope=FULL_USER_SCOPE,
            name=key_1_ref,
            value="myval1",
        )
        kvp_1_db = KeyValuePair.add_or_update(kvp_1_db)
        self.resources[kvp_1_db.uid] = kvp_1_db

        key_2_name = "mykey2"
        key_2_ref = get_key_reference(FULL_USER_SCOPE, key_2_name, user_1_db.name)
        kvp_2_db = KeyValuePairDB(
            uid="%s:%s:%s" % (ResourceType.KEY_VALUE_PAIR, FULL_USER_SCOPE, key_2_ref),
            scope=FULL_USER_SCOPE,
            name=key_2_ref,
            value="myval2",
        )
        kvp_2_db = KeyValuePair.add_or_update(kvp_2_db)
        self.resources[kvp_2_db.uid] = kvp_2_db

        # User1 should have general list permissions on user1's kvps.
        self.assertUserHasResourceDbPermission(
            resolver=resolver,
            user_db=user_1_db,
            resource_db=KeyValuePairDB(scope="%s:%s" % (FULL_USER_SCOPE, user_1_db.name)),
            permission_type=PermissionType.KEY_VALUE_PAIR_LIST,
        )

        # User1 should have all, read, and write permissions on user1's kvps.
        for k in [key_1_name, key_2_name]:
            kvp_ref = get_key_reference(FULL_USER_SCOPE, k, user_1_db.name)
            kvp_uid = "%s:%s:%s" % (ResourceType.KEY_VALUE_PAIR, FULL_USER_SCOPE, kvp_ref)
            kvp_db = self.resources[kvp_uid]

            self.assertUserHasResourceDbPermission(
                resolver=resolver,
                user_db=user_1_db,
                resource_db=kvp_db,
                permission_type=PermissionType.KEY_VALUE_PAIR_ALL,
            )

            self.assertUserHasResourceDbPermissions(
                resolver=resolver,
                user_db=user_1_db,
                resource_db=kvp_db,
                permission_types=self.read_permission_types,
            )

            self.assertUserHasResourceDbPermissions(
                resolver=resolver,
                user_db=user_1_db,
                resource_db=kvp_db,
                permission_types=self.write_permission_types,
            )

        # User2 should not have general list permissions on user1's kvps.
        self.assertUserDoesntHaveResourceDbPermission(
            resolver=resolver,
            user_db=user_2_db,
            resource_db=KeyValuePairDB(scope="%s:%s" % (FULL_USER_SCOPE, user_1_db.name)),
            permission_type=PermissionType.KEY_VALUE_PAIR_LIST,
        )

        # User2 should not have any permissions on user1's kvps.
        for k in [key_1_name, key_2_name]:
            kvp_ref = get_key_reference(FULL_USER_SCOPE, k, user_1_db.name)
            kvp_uid = "%s:%s:%s" % (ResourceType.KEY_VALUE_PAIR, FULL_USER_SCOPE, kvp_ref)
            kvp_db = self.resources[kvp_uid]

            self.assertUserDoesntHaveResourceDbPermission(
                resolver=resolver,
                user_db=user_2_db,
                resource_db=kvp_db,
                permission_type=PermissionType.KEY_VALUE_PAIR_ALL,
            )

            self.assertUserDoesntHaveResourceDbPermissions(
                resolver=resolver,
                user_db=user_2_db,
                resource_db=kvp_db,
                permission_types=self.read_permission_types,
            )

            self.assertUserDoesntHaveResourceDbPermissions(
                resolver=resolver,
                user_db=user_2_db,
                resource_db=kvp_db,
                permission_types=self.write_permission_types,
            )

    def test_user_permissions_for_another_user_kvps(self):
        resolver = KeyValuePermissionsResolver()

        # Setup users. No explicit grant, role, and assignment records should be
        # required for user to access their KVPs
        user_1_db = UserDB(name="user103")
        user_1_db = User.add_or_update(user_1_db)
        self.users[user_1_db.name] = user_1_db

        user_2_db = UserDB(name="user104")
        user_2_db = User.add_or_update(user_2_db)
        self.users[user_2_db.name] = user_2_db

        # Insert user scoped key value pairs for user1.
        key_1_name = "mykey3"
        key_1_ref = get_key_reference(FULL_USER_SCOPE, key_1_name, user_1_db.name)
        kvp_1_db = KeyValuePairDB(
            uid="%s:%s:%s" % (ResourceType.KEY_VALUE_PAIR, FULL_USER_SCOPE, key_1_ref),
            scope=FULL_USER_SCOPE,
            name=key_1_ref,
            value="myval3",
        )
        kvp_1_db = KeyValuePair.add_or_update(kvp_1_db)
        self.resources[kvp_1_db.uid] = kvp_1_db

        # Setup bad grant, role, and assignment records where administrator
        # accidentally or intentionally try to grant a user's kvps to another user.
        grant_db = PermissionGrantDB(
            resource_uid=kvp_1_db.get_uid(),
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_PAIR_ALL],
        )
        grant_db = PermissionGrant.add_or_update(grant_db)

        role_db = RoleDB(
            name="custom_role_user_key3_all_grant",
            permission_grants=[str(grant_db.id)],
        )
        role_db = Role.add_or_update(role_db)
        self.roles[role_db.name] = role_db

        role_assignment_db = UserRoleAssignmentDB(
            user=user_2_db.name,
            role=role_db.name,
            source="assignments/%s.yaml" % user_2_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        # User2 should not have general list permissions on user1's kvps.
        self.assertUserDoesntHaveResourceDbPermission(
            resolver=resolver,
            user_db=user_2_db,
            resource_db=KeyValuePairDB(scope="%s:%s" % (FULL_USER_SCOPE, user_1_db.name)),
            permission_type=PermissionType.KEY_VALUE_PAIR_LIST,
        )

        # User2 should not have any permissions on another user1's kvp.
        self.assertUserDoesntHaveResourceDbPermission(
            resolver=resolver,
            user_db=user_2_db,
            resource_db=kvp_1_db,
            permission_type=PermissionType.KEY_VALUE_PAIR_ALL,
        )

        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_2_db,
            resource_db=kvp_1_db,
            permission_types=self.read_permission_types,
        )

        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_2_db,
            resource_db=kvp_1_db,
            permission_types=self.write_permission_types,
        )

    def test_admin_permissions_for_user_scoped_kvps(self):
        resolver = KeyValuePermissionsResolver()

        admin_user_db = self.users["admin"]

        # Setup users. No explicit grant, role, and assignment records should be
        # required for user to access their KVPs
        user_1_db = UserDB(name="user105")
        user_1_db = User.add_or_update(user_1_db)
        self.users[user_1_db.name] = user_1_db

        # Insert user scoped key value pairs for user1.
        key_1_name = "mykey5"
        key_1_ref = get_key_reference(FULL_USER_SCOPE, key_1_name, user_1_db.name)
        kvp_1_db = KeyValuePairDB(
            uid="%s:%s:%s" % (ResourceType.KEY_VALUE_PAIR, FULL_USER_SCOPE, key_1_ref),
            scope=FULL_USER_SCOPE,
            name=key_1_ref,
            value="myval5",
        )
        kvp_1_db = KeyValuePair.add_or_update(kvp_1_db)
        self.resources[kvp_1_db.uid] = kvp_1_db

        # Admin user should not have general list permissions on user1's kvps.
        self.assertUserDoesntHaveResourceDbPermission(
            resolver=resolver,
            user_db=admin_user_db,
            resource_db=KeyValuePairDB(scope="%s:%s" % (FULL_USER_SCOPE, user_1_db.name)),
            permission_type=PermissionType.KEY_VALUE_PAIR_LIST,
        )

        # User2 should not have any permissions on another user1's kvp.
        self.assertUserDoesntHaveResourceDbPermission(
            resolver=resolver,
            user_db=admin_user_db,
            resource_db=kvp_1_db,
            permission_type=PermissionType.KEY_VALUE_PAIR_ALL,
        )

        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=admin_user_db,
            resource_db=kvp_1_db,
            permission_types=self.read_permission_types,
        )

        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=admin_user_db,
            resource_db=kvp_1_db,
            permission_types=self.write_permission_types,
        )
