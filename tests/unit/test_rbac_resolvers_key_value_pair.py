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

from st2rbac_backend.resolvers import KeyValuePermissionsResolver
from tests.unit.test_rbac_resolvers import BasePermissionsResolverTestCase

__all__ = ["KeyValuePermissionsResolver"]


class KeyValueSystemScopePermissionsResolverTestCase(BasePermissionsResolverTestCase):
    def setUp(self):
        super(KeyValueSystemScopePermissionsResolverTestCase, self).setUp()

    def test_user_resource_db_no_role_permissions(self):
        resolver = KeyValuePermissionsResolver()

        # Insert mock user
        user_1_db = UserDB(name="1_role_view_grant")
        user_1_db = User.add_or_update(user_1_db)
        self.users["custom_role_key_value_pair_view_grant"] = user_1_db

        # Insert mock data
        kvp_1_db = KeyValuePairDB(
            uid="key_value_pair:st2kv.system:key1",
            scope="st2kv.system",
            name="key1",
            value="val1",
        )
        kvp_1_db = KeyValuePair.add_or_update(kvp_1_db)
        self.resources["user_role_1"] = kvp_1_db

        all_permission_types = PermissionType.get_valid_permissions_for_resource_type(
            ResourceType.KEY_VALUE_PAIR
        )

        resource_db = self.resources["user_role_1"]
        # No roles, should return false for everything
        user_db = self.users["no_roles"]
        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=resource_db,
            permission_types=all_permission_types,
        )

        # Custom role with no permission grants, should return false for everything
        user_db = self.users["1_custom_role_no_permissions"]
        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=resource_db,
            permission_types=all_permission_types,
        )

    def test_user_no_role_permissions(self):
        resolver = KeyValuePermissionsResolver()
        permission_type = PermissionType.KEY_VALUE_LIST

        # Custom role with no permission grants, should return false for everything
        user_db = self.users["1_custom_role_no_permissions"]
        self.assertUserDoesntHavePermission(
            resolver=resolver, user_db=user_db, permission_type=permission_type
        )

        # No roles, should return false for everything
        user_db = self.users["no_roles"]
        self.assertUserDoesntHavePermission(
            resolver=resolver, user_db=user_db, permission_type=permission_type
        )

    def test_admin_get_all_system_success(self):
        resolver = KeyValuePermissionsResolver()
        all_permission_types = PermissionType.get_valid_permissions_for_resource_type(
            ResourceType.KEY_VALUE_PAIR
        )

        kvp_1_db = KeyValuePairDB(
            uid="key_value_pair:st2kv.system:key1",
            scope="st2kv.system",
            name="key1",
            value="val1",
        )
        kvp_1_db = KeyValuePair.add_or_update(kvp_1_db)
        self.resources["user_role_1"] = kvp_1_db

        # Admin user, should always return true
        resource_db = self.resources["user_role_1"]
        user_db = self.users["admin"]

        self.assertUserHasResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=resource_db,
            permission_types=all_permission_types,
        )

    def test_observer_get_all_system_success(self):
        resolver = KeyValuePermissionsResolver()

        kvp_2_db = KeyValuePairDB(
            uid="key_value_pair:st2kv.system:key2",
            scope="st2kv.system",
            name="key2",
            value="val2",
        )
        kvp_2_db = KeyValuePair.add_or_update(kvp_2_db)
        self.resources["user_role_2"] = kvp_2_db

        # Observer should always return true for VIEW, LIST permissions
        user_db = self.users["observer"]

        self.assertUserHasResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=self.resources["user_role_2"],
            permission_types=[
                PermissionType.KEY_VALUE_VIEW,
                PermissionType.KEY_VALUE_LIST,
            ],
        )

    def test_observer_get_all_system_failure(self):
        resolver = KeyValuePermissionsResolver()
        kvp_3_db = KeyValuePairDB(
            uid="key_value_pair:st2kv.system:key3",
            scope="st2kv.system",
            name="key3",
            value="val3",
        )
        kvp_3_db = KeyValuePair.add_or_update(kvp_3_db)
        self.resources["user_role_3"] = kvp_3_db

        # Observer, should always return false for DELETE, SET permissions
        user_db = self.users["observer"]
        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=self.resources["user_role_3"],
            permission_types=[
                PermissionType.KEY_VALUE_DELETE,
                PermissionType.KEY_VALUE_SET,
            ],
        )

    def test_get_all_user_permissions_success(self):
        resolver = KeyValuePermissionsResolver()

        user_2_db = UserDB(name="2_role_list_grant")
        user_2_db = User.add_or_update(user_2_db)
        self.users["custom_role_key_value_pair_list_grant"] = user_2_db

        kvp_2_db = KeyValuePairDB(
            uid="key_value_pair:st2kv.system:",
            scope="st2kv.system",
            name="",
            value="",
        )
        kvp_2_db = KeyValuePair.add_or_update(kvp_2_db)
        self.resources["user_role_2"] = kvp_2_db

        grant_db = PermissionGrantDB(
            resource_uid=self.resources["user_role_2"].get_uid(),
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_LIST],
        )
        grant_db = PermissionGrant.add_or_update(grant_db)
        permission_grants = [str(grant_db.id)]
        role_2_db = RoleDB(
            name="custom_role_key_value_pair_list_grant",
            permission_grants=permission_grants,
        )
        role_2_db = Role.add_or_update(role_2_db)
        self.roles["custom_role_key_value_pair_list_grant"] = role_2_db

        user_db = self.users["custom_role_key_value_pair_list_grant"]
        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=self.roles["custom_role_key_value_pair_list_grant"].name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        # Custom user role with LIST on specific system scope KVPs
        user_db = self.users["custom_role_key_value_pair_list_grant"]
        self.assertUserHasResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=self.resources["user_role_2"],
            permission_types=[
                PermissionType.KEY_VALUE_LIST,
                PermissionType.KEY_VALUE_VIEW,
            ],
        )

        # Custom user role with no VIEW/DELETE/SET permissions
        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=self.resources["user_role_2"],
            permission_types=[
                PermissionType.KEY_VALUE_SET,
                PermissionType.KEY_VALUE_DELETE,
            ],
        )

    def test_get_user_permission(self):
        resolver = KeyValuePermissionsResolver()

        user_1_db = UserDB(name="1_role_view_grant")
        user_1_db = User.add_or_update(user_1_db)
        self.users["custom_role_key_value_pair_view_grant"] = user_1_db

        kvp_1_db = KeyValuePairDB(
            uid="key_value_pair:st2kv.system:key1",
            scope="st2kv.system",
            name="key1",
            value="val1",
        )
        kvp_1_db = KeyValuePair.add_or_update(kvp_1_db)
        self.resources["user_role_1"] = kvp_1_db

        grant_db = PermissionGrantDB(
            resource_uid=self.resources["user_role_1"].get_uid(),
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[
                PermissionType.KEY_VALUE_VIEW,
                PermissionType.KEY_VALUE_LIST,
            ],
        )
        grant_db = PermissionGrant.add_or_update(grant_db)
        permission_grants = [str(grant_db.id)]

        role_1_db = RoleDB(
            name="custom_role_key_value_pair_view_grant",
            permission_grants=permission_grants,
        )
        role_1_db = Role.add_or_update(role_1_db)
        self.roles["custom_role_key_value_pair_view_grant"] = role_1_db

        user_db = self.users["custom_role_key_value_pair_view_grant"]
        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=self.roles["custom_role_key_value_pair_view_grant"].name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        # Custom user role with VIEW/LIST permissions on specific system scope KVPs
        user_db = self.users["custom_role_key_value_pair_view_grant"]
        self.assertUserHasResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=self.resources["user_role_1"],
            permission_types=[
                PermissionType.KEY_VALUE_VIEW,
                PermissionType.KEY_VALUE_LIST,
            ],
        )

        # Custom user role with no SET/DELETE permissions
        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=self.resources["user_role_1"],
            permission_types=[
                PermissionType.KEY_VALUE_SET,
                PermissionType.KEY_VALUE_DELETE,
            ],
        )

    def test_set_user_permission(self):
        resolver = KeyValuePermissionsResolver()

        user_4_db = UserDB(name="4_role_create_grant")
        user_4_db = User.add_or_update(user_4_db)
        self.users["custom_role_key_value_pair_create_grant"] = user_4_db

        kvp_4_db = KeyValuePairDB(
            uid="key_value_pair:st2kv.system:key4",
            scope="st2kv.system",
            name="key4",
            value="val4",
        )
        kvp_4_db = KeyValuePair.add_or_update(kvp_4_db)
        self.resources["user_role_4"] = kvp_4_db

        grant_db = PermissionGrantDB(
            resource_uid=self.resources["user_role_4"].get_uid(),
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_SET],
        )
        grant_db = PermissionGrant.add_or_update(grant_db)
        permission_grants = [str(grant_db.id)]

        role_4_db = RoleDB(
            name="custom_role_key_value_pair_create_grant",
            permission_grants=permission_grants,
        )
        role_4_db = Role.add_or_update(role_4_db)
        self.roles["custom_role_key_value_pair_create_grant"] = role_4_db

        user_db = self.users["custom_role_key_value_pair_create_grant"]
        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=self.roles["custom_role_key_value_pair_create_grant"].name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        user_db = self.users["custom_role_key_value_pair_create_grant"]

        # Custom user role with SET/VIEW permissions on specific system scope KVPs
        self.assertUserHasResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=self.resources["user_role_4"],
            permission_types=[
                PermissionType.KEY_VALUE_SET,
                PermissionType.KEY_VALUE_VIEW,
            ],
        )

        # Custom user role with no LIST/DELETE permissions
        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=self.resources["user_role_4"],
            permission_types=[
                PermissionType.KEY_VALUE_LIST,
                PermissionType.KEY_VALUE_DELETE,
            ],
        )

    def test_delete_user_permission(self):
        resolver = KeyValuePermissionsResolver()

        user_5_db = UserDB(name="5_role_delete_grant")
        user_5_db = User.add_or_update(user_5_db)
        self.users["custom_role_key_value_pair_delete_grant"] = user_5_db

        kvp_5_db = KeyValuePairDB(
            uid="key_value_pair:st2kv.system:key5",
            scope="st2kv.system",
            name="key5",
            value="val5",
        )
        kvp_5_db = KeyValuePair.add_or_update(kvp_5_db)
        self.resources["user_role_5"] = kvp_5_db

        grant_db = PermissionGrantDB(
            resource_uid=self.resources["user_role_5"].get_uid(),
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_DELETE],
        )
        grant_db = PermissionGrant.add_or_update(grant_db)
        permission_grants = [str(grant_db.id)]

        role_5_db = RoleDB(
            name="custom_role_key_value_pair_delete_grant",
            permission_grants=permission_grants,
        )
        role_5_db = Role.add_or_update(role_5_db)
        self.roles["custom_role_key_value_pair_delete_grant"] = role_5_db

        user_db = self.users["custom_role_key_value_pair_delete_grant"]
        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=self.roles["custom_role_key_value_pair_delete_grant"].name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        user_db = self.users["custom_role_key_value_pair_delete_grant"]

        # Custom user role with DELETE/VIEW permissions on specific system scope KVPs
        self.assertUserHasResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=self.resources["user_role_5"],
            permission_types=[
                PermissionType.KEY_VALUE_DELETE,
                PermissionType.KEY_VALUE_VIEW,
            ],
        )

        # Custom user role with no LIST/SET permissions
        self.assertUserDoesntHaveResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=self.resources["user_role_5"],
            permission_types=[
                PermissionType.KEY_VALUE_LIST,
                PermissionType.KEY_VALUE_SET,
            ],
        )


class KeyValueUserScopePermissionsResolverTestCase(BasePermissionsResolverTestCase):
    def setUp(self):
        super(KeyValueUserScopePermissionsResolverTestCase, self).setUp()

    def test_get_all_user_permissions_success(self):

        resolver = KeyValuePermissionsResolver()
        user_1_db = UserDB(name="testuser")
        user_1_db = User.add_or_update(user_1_db)
        self.users["testuser"] = user_1_db
        all_permission_types = PermissionType.get_valid_permissions_for_resource_type(
            ResourceType.KEY_VALUE_PAIR
        )

        kvp_1_db = KeyValuePairDB(
            uid="key_value_pair:st2kv.user:testuser:key1",
            scope="st2kv.user",
            name="key1",
            value="val1",
        )
        kvp_1_db = KeyValuePair.add_or_update(kvp_1_db)
        self.resources["user_role_1"] = kvp_1_db

        resource_db = self.resources["user_role_1"]

        grant_db = PermissionGrantDB(
            resource_uid=self.resources["user_role_1"].get_uid(),
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_ALL],
        )
        grant_db = PermissionGrant.add_or_update(grant_db)
        permission_grants = [str(grant_db.id)]

        role_1_db = RoleDB(
            name="key_value_pair_all_grant",
            permission_grants=permission_grants,
        )
        role_1_db = Role.add_or_update(role_1_db)
        self.roles["key_value_pair_all_grant"] = role_1_db

        user_db = self.users["testuser"]
        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=self.roles["key_value_pair_all_grant"].name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        # Default for user on user owned KVPs
        self.assertUserHasResourceDbPermissions(
            resolver=resolver,
            user_db=user_db,
            resource_db=resource_db,
            permission_types=all_permission_types,
        )

    def test_get_system_key_user_permissions_success(self):

        resolver = KeyValuePermissionsResolver()
        user_1_db = UserDB(name="testuser1")
        user_1_db = User.add_or_update(user_1_db)
        self.users["testuser1"] = user_1_db

        kvp_1_db = KeyValuePairDB(
            uid="key_value_pair:st2kv.system:key1",
            scope="st2kv.system",
            name="key1",
            value="val1",
        )
        kvp_1_db = KeyValuePair.add_or_update(kvp_1_db)
        self.resources["user_role_2"] = kvp_1_db

        resource_db = self.resources["user_role_2"]

        grant_db = PermissionGrantDB(
            resource_uid=self.resources["user_role_2"].get_uid(),
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_VIEW],
        )
        grant_db = PermissionGrant.add_or_update(grant_db)
        permission_grants = [str(grant_db.id)]

        role_1_db = RoleDB(
            name="key_value_pair_list_grant",
            permission_grants=permission_grants,
        )
        role_1_db = Role.add_or_update(role_1_db)
        self.roles["key_value_pair_list_grant"] = role_1_db

        user_db = self.users["testuser1"]
        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=self.roles["key_value_pair_list_grant"].name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        # Default for user on user owned KVPs
        self.assertUserHasResourceDbPermission(
            resolver=resolver,
            user_db=user_db,
            resource_db=resource_db,
            permission_type=PermissionType.KEY_VALUE_VIEW,
        )

    def test_set_system_key_user_permissions_success(self):

        resolver = KeyValuePermissionsResolver()
        user_1_db = UserDB(name="testuser1")
        user_1_db = User.add_or_update(user_1_db)
        self.users["testuser1"] = user_1_db

        kvp_1_db = KeyValuePairDB(
            uid="key_value_pair:st2kv.system:key2",
            scope="st2kv.system",
            name="key2",
            value="val2",
        )
        kvp_1_db = KeyValuePair.add_or_update(kvp_1_db)
        self.resources["user_role_3"] = kvp_1_db

        resource_db = self.resources["user_role_3"]

        grant_db = PermissionGrantDB(
            resource_uid=self.resources["user_role_3"].get_uid(),
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_SET],
        )
        grant_db = PermissionGrant.add_or_update(grant_db)
        permission_grants = [str(grant_db.id)]

        role_1_db = RoleDB(
            name="key_value_pair_create_grant",
            permission_grants=permission_grants,
        )
        role_1_db = Role.add_or_update(role_1_db)
        self.roles["key_value_pair_create_grant"] = role_1_db

        user_db = self.users["testuser1"]
        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=self.roles["key_value_pair_create_grant"].name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        # Default for user on user owned KVPs
        self.assertUserHasResourceDbPermission(
            resolver=resolver,
            user_db=user_db,
            resource_db=resource_db,
            permission_type=PermissionType.KEY_VALUE_SET,
        )

    def test_delete_system_key_user_permissions_success(self):

        resolver = KeyValuePermissionsResolver()
        user_1_db = UserDB(name="testuser1")
        user_1_db = User.add_or_update(user_1_db)
        self.users["testuser1"] = user_1_db

        kvp_1_db = KeyValuePairDB(
            uid="key_value_pair:st2kv.system:key1",
            scope="st2kv.system",
            name="key2",
            value="val2",
        )
        kvp_1_db = KeyValuePair.add_or_update(kvp_1_db)
        self.resources["user_role_4"] = kvp_1_db

        resource_db = self.resources["user_role_4"]

        grant_db = PermissionGrantDB(
            resource_uid=self.resources["user_role_4"].get_uid(),
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_DELETE],
        )
        grant_db = PermissionGrant.add_or_update(grant_db)
        permission_grants = [str(grant_db.id)]

        role_1_db = RoleDB(
            name="key_value_pair_delete_grant",
            permission_grants=permission_grants,
        )
        role_1_db = Role.add_or_update(role_1_db)
        self.roles["key_value_pair_delete_grant"] = role_1_db

        user_db = self.users["testuser1"]
        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=self.roles["key_value_pair_delete_grant"].name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        # Default for user on user owned KVPs
        self.assertUserHasResourceDbPermission(
            resolver=resolver,
            user_db=user_db,
            resource_db=resource_db,
            permission_type=PermissionType.KEY_VALUE_DELETE,
        )
