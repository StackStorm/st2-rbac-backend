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

import six

from st2common.constants.keyvalue import FULL_SYSTEM_SCOPE
from st2common.constants.keyvalue import FULL_USER_SCOPE
from st2common.services.keyvalues import get_key_reference
from st2common.persistence.auth import User
from st2common.models.db.auth import UserDB
from st2common.models.db.keyvalue import KeyValuePairDB
from st2common.persistence.keyvalue import KeyValuePair
from st2common.models.api.keyvalue import KeyValuePairSetAPI
from st2common.models.api.keyvalue import KeyValuePairAPI
from st2common.models.db.rbac import UserRoleAssignmentDB
from st2common.models.db.rbac import PermissionGrantDB
from st2common.rbac.types import PermissionType
from st2common.rbac.types import ResourceType
from st2common.persistence.rbac import UserRoleAssignment
from st2common.persistence.rbac import PermissionGrant
from st2common.persistence.rbac import Role
from st2common.models.db.rbac import RoleDB

from tests.base import APIControllerWithRBACTestCase

http_client = six.moves.http_client

__all__ = ["KeyValuesControllerRBACTestCase"]


class KeyValuesControllerRBACTestCase(APIControllerWithRBACTestCase):
    def setUp(self):
        super(KeyValuesControllerRBACTestCase, self).setUp()

        self.kvps = {}

        # Insert mock users
        user_1_db = UserDB(name="user1")
        user_1_db = User.add_or_update(user_1_db)
        self.users["user_1"] = user_1_db

        # Insert mock kvp objects
        kvp_api = KeyValuePairSetAPI(
            name="test_system_scope", value="value1", scope=FULL_SYSTEM_SCOPE
        )
        kvp_db = KeyValuePairSetAPI.to_model(kvp_api)
        kvp_db = KeyValuePair.add_or_update(kvp_db)
        kvp_db = KeyValuePairAPI.from_model(kvp_db)
        self.kvps["kvp_1"] = kvp_db

        name = get_key_reference(
            scope=FULL_USER_SCOPE, name="test_user_scope_1", user="user1"
        )
        kvp_db = KeyValuePairDB(name=name, value="valueu12", scope=FULL_USER_SCOPE)
        kvp_db = KeyValuePair.add_or_update(kvp_db)
        kvp_db = KeyValuePairAPI.from_model(kvp_db)
        self.kvps["kvp_3"] = kvp_db

        name = get_key_reference(
            scope=FULL_USER_SCOPE, name="test_user_scope_3", user="user2"
        )
        kvp_db = KeyValuePairDB(name=name, value="valueu21", scope=FULL_USER_SCOPE)
        kvp_db = KeyValuePair.add_or_update(kvp_db)
        kvp_db = KeyValuePairAPI.from_model(kvp_db)
        self.kvps["kvp_5"] = kvp_db

        name = get_key_reference(
            scope=FULL_USER_SCOPE, name="test_user_scope_4", user="user4"
        )
        kvp_db = KeyValuePairDB(name=name, value="valueu121", scope=FULL_USER_SCOPE)
        kvp_db = KeyValuePair.add_or_update(kvp_db)
        kvp_db = KeyValuePairAPI.from_model(kvp_db)
        self.kvps["kvp_6"] = kvp_db

        name = get_key_reference(
            scope=FULL_USER_SCOPE, name="test_user_scope_1", user="user5"
        )
        kvp_db = KeyValuePairDB(name=name, value="valueu122", scope=FULL_USER_SCOPE)
        kvp_db = KeyValuePair.add_or_update(kvp_db)
        kvp_db = KeyValuePairAPI.from_model(kvp_db)
        self.kvps["kvp_7"] = kvp_db

        name = get_key_reference(
            scope=FULL_USER_SCOPE, name="test_user_scope_8", user="user5"
        )
        kvp_db = KeyValuePairDB(name=name, value="valueu22", scope=FULL_USER_SCOPE)
        kvp_db = KeyValuePair.add_or_update(kvp_db)
        kvp_db = KeyValuePairAPI.from_model(kvp_db)
        self.kvps["kvp_8"] = kvp_db

        # key_value_pair_set grant permissions on user
        # list permission type for user
        grant_1_db = PermissionGrantDB(
            resource_uid="key_value_pair:st2kv.user:user1:",
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_LIST],
        )
        grant_1_db = PermissionGrant.add_or_update(grant_1_db)
        # view permission type for user
        grant_10_db = PermissionGrantDB(
            resource_uid="key_value_pair:st2kv.user:user1:test_user_scope_3",
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_VIEW],
        )
        grant_10_db = PermissionGrant.add_or_update(grant_10_db)
        grant_11_db = PermissionGrantDB(
            resource_uid="key_value_pair:st2kv.user:user1:test_user_scope_2",
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_VIEW],
        )
        grant_11_db = PermissionGrant.add_or_update(grant_11_db)
        grant_12_db = PermissionGrantDB(
            resource_uid="key_value_pair:st2kv.user:user1:test_user_scope_1",
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_VIEW],
        )
        grant_12_db = PermissionGrant.add_or_update(grant_12_db)

        # key_value_pair_set grant permissions on system
        grant_13_db = PermissionGrantDB(
            resource_uid="key_value_pair:st2kv.system:user1:test_system_scope",
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_VIEW],
        )
        grant_13_db = PermissionGrant.add_or_update(grant_13_db)

        # delete permission type for system user
        grant_14_db = PermissionGrantDB(
            resource_uid="key_value_pair:st2kv.system:test_system_scope",
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_DELETE],
        )
        grant_14_db = PermissionGrant.add_or_update(grant_14_db)
        permission_grants = [
            str(grant_1_db.id),
            str(grant_10_db.id),
            str(grant_11_db.id),
            str(grant_12_db.id),
            str(grant_13_db.id),
            str(grant_14_db.id),
        ]
        role_1_db = RoleDB(name="user1", permission_grants=permission_grants)
        role_1_db = Role.add_or_update(role_1_db)
        self.roles["user_1"] = role_1_db

        user_db = self.users["user_1"]
        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=self.roles["user_1"].name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

    def test_get_all_system_scope_success(self):
        # mock user
        user_2_db = UserDB(name="user2")
        user_2_db = User.add_or_update(user_2_db)
        self.users["user_2"] = user_2_db

        # role assignemnt
        grant_db = PermissionGrantDB(
            resource_uid="key_value_pair:st2kv.system:",
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_LIST],
        )
        grant_db = PermissionGrant.add_or_update(grant_db)
        grant_9_db = PermissionGrantDB(
            resource_uid="key_value_pair:st2kv.user:user2:test_user_scope_3",
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_VIEW],
        )
        grant_9_db = PermissionGrant.add_or_update(grant_9_db)
        permission_grants = [str(grant_db.id), str(grant_9_db.id)]
        role_1_db = RoleDB(name="user_2", permission_grants=permission_grants)
        role_1_db = Role.add_or_update(role_1_db)
        self.roles["user_2"] = role_1_db

        user_db = self.users["user_2"]
        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=self.roles["user_2"].name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        # Regular user, should be able to view all the system scoped items
        self.use_user(self.users["user_2"])

        resp = self.app.get("/v1/keys")
        self.assertEqual(resp.status_int, 200)
        for item in resp.json:
            self.assertEqual(item["scope"], FULL_SYSTEM_SCOPE)

        # limit=-1 admin user
        self.use_user(self.users["admin"])
        resp = self.app.get("/v1/keys/?limit=-1")
        self.assertEqual(resp.status_int, 200)
        for item in resp.json:
            self.assertEqual(item["scope"], FULL_SYSTEM_SCOPE)

    def test_get_all_user_scope_success(self):
        # Regular user should be able to view all the items scoped to themselves
        self.use_user(self.users["user_1"])

        resp = self.app.get("/v1/keys?scope=st2kv.user")
        self.assertEqual(resp.status_int, 200)
        for item in resp.json:
            self.assertEqual(item["scope"], FULL_USER_SCOPE)
            self.assertEqual(item["user"], "user1")

    def test_get_all_scope_system_decrypt_admin_success(self):
        # Admin should be able to view all system scoped decrypted values
        self.use_user(self.users["admin"])

        resp = self.app.get("/v1/keys?decrypt=True")
        self.assertEqual(resp.status_int, 200)
        for item in resp.json:
            self.assertEqual(item["scope"], FULL_SYSTEM_SCOPE)

    def test_get_all_scope_all_admin_decrypt_success(self):
        # Admin users should be able to view all items (including user scoped ones) when using
        # ?scope=all
        self.use_user(self.users["admin"])

        resp = self.app.get("/v1/keys?scope=all&decrypt=True")
        self.assertEqual(resp.status_int, 200)

        # Verify user scoped items are available and decrypted
        self.assertEqual(resp.json[3]["scope"], FULL_USER_SCOPE)
        self.assertEqual(resp.json[3]["user"], "user4")
        self.assertEqual(resp.json[3]["value"], "valueu121")

        self.assertEqual(resp.json[4]["scope"], FULL_USER_SCOPE)
        self.assertEqual(resp.json[4]["user"], "user5")

        resp = self.app.get("/v1/keys?scope=all&decrypt=True&limit=-1")
        self.assertEqual(resp.status_int, 200)

    def test_get_all_non_admin_decrypt_failure(self):
        # Non admin shouldn't be able to view decrypted items
        self.use_user(self.users["user_1"])

        resp = self.app.get("/v1/keys?decrypt=True", expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)
        self.assertTrue(
            "Decrypt option requires administrator access" in resp.json["faultstring"]
        )

    def test_get_all_scope_all_non_admin_failure(self):
        # Non admin users can't use scope=all
        self.use_user(self.users["user_1"])

        resp = self.app.get("/v1/keys?scope=all", expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)
        self.assertTrue(
            '"all" scope requires administrator access' in resp.json["faultstring"]
        )

    def test_get_one_system_scope_success(self):
        user_3_db = UserDB(name="user3")
        user_3_db = User.add_or_update(user_3_db)
        self.users["user_3"] = user_3_db

        # view permission type for system user
        grant_2_db = PermissionGrantDB(
            resource_uid="key_value_pair:st2kv.system:user3:test_system_scope",
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_VIEW],
        )
        grant_2_db = PermissionGrant.add_or_update(grant_2_db)
        permission_grants = [str(grant_2_db.id)]
        role_1_db = RoleDB(name="user3", permission_grants=permission_grants)
        role_1_db = Role.add_or_update(role_1_db)
        self.roles["user_3"] = role_1_db

        user_db = self.users["user_3"]
        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=self.roles["user_3"].name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        self.use_user(self.users["user_3"])

        resp = self.app.get("/v1/keys/%s" % (self.kvps["kvp_1"].name))
        self.assertEqual(resp.json["scope"], FULL_SYSTEM_SCOPE)

    def test_get_one_user_scope_success(self):
        # Retrieving user scoped variable which is scoped to the authenticated user
        self.use_user(self.users["user_1"])

        resp = self.app.get("/v1/keys/%s?scope=st2kv.user" % (self.kvps["kvp_3"].name))
        self.assertEqual(resp.json["scope"], FULL_USER_SCOPE)
        self.assertEqual(resp.json["user"], "user1")

    def test_get_one_user_scope_decrypt_success(self):
        name = get_key_reference(
            scope=FULL_USER_SCOPE, name="test_user_scope_2", user="user1"
        )
        kvp_api = KeyValuePairSetAPI(
            name=name, value="user_secret", scope=FULL_USER_SCOPE, secret=True
        )
        kvp_db = KeyValuePairSetAPI.to_model(kvp_api)
        kvp_db = KeyValuePair.add_or_update(kvp_db)
        kvp_db = KeyValuePairAPI.from_model(kvp_db)
        self.kvps["kvp_4"] = kvp_db

        # User can request decrypted value of the item scoped to themselves
        self.use_user(self.users["user_1"])

        resp = self.app.get(
            "/v1/keys/%s?scope=st2kv.user&decrypt=True" % (self.kvps["kvp_4"].name)
        )
        self.assertEqual(resp.json["scope"], FULL_USER_SCOPE)
        self.assertEqual(resp.json["user"], "user1")
        self.assertTrue(resp.json["secret"])
        self.assertEqual(resp.json["value"], "user_secret")

    def test_get_one_user_scope_non_current_user_failure(self):
        # mock user
        user_2_db = UserDB(name="user2")
        user_2_db = User.add_or_update(user_2_db)
        self.users["user_2"] = user_2_db

        grant_db = PermissionGrantDB(
            resource_uid="key_value_pair:st2kv.system:",
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_LIST],
        )
        grant_db = PermissionGrant.add_or_update(grant_db)
        grant_9_db = PermissionGrantDB(
            resource_uid="key_value_pair:st2kv.user:user2:test_user_scope_3",
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_VIEW],
        )
        grant_9_db = PermissionGrant.add_or_update(grant_9_db)
        permission_grants = [str(grant_db.id), str(grant_9_db.id)]
        role_1_db = RoleDB(name="user_2", permission_grants=permission_grants)
        role_1_db = Role.add_or_update(role_1_db)
        self.roles["user_2"] = role_1_db

        # role assignemnt
        user_db = self.users["user_2"]
        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=self.roles["user_2"].name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)
        # User should only be able to retrieved user-scoped items which are scoped to themselves
        self.use_user(self.users["user_1"])

        # This item is scoped to user2
        resp = self.app.get(
            "/v1/keys/%s?scope=st2kv.user" % (self.kvps["kvp_5"].name),
            expect_errors=True,
        )
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)

        # Should work fine for other user
        self.use_user(self.users["user_2"])

        resp = self.app.get("/v1/keys/%s?scope=st2kv.user" % (self.kvps["kvp_5"].name))
        self.assertEqual(resp.json["scope"], FULL_USER_SCOPE)
        self.assertEqual(resp.json["user"], "user2")

    def test_get_one_system_scope_decrypt_non_admin_user_failure(self):
        # Non-admin user can't access decrypted system scoped items. They can only access decrypted
        # items which are scoped to themselves.
        self.use_user(self.users["user_1"])

        resp = self.app.get(
            "/v1/keys/%s?decrypt=True" % (self.kvps["kvp_1"].name), expect_errors=True
        )
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)
        self.assertTrue(
            "Decrypt option requires administrator access" in resp.json["faultstring"]
        )

    def test_set_user_scoped_item_arbitrary_user_admin_success(self):
        # Admin user can set user-scoped items for an arbitrary user
        self.use_user(self.users["admin"])

        data = {
            "name": "test_new_key_1",
            "value": "testvalue1",
            "scope": FULL_USER_SCOPE,
            "user": "user2",
        }
        resp = self.app.put_json("/v1/keys/test_new_key_1", data)
        self.assertEqual(resp.status_code, http_client.OK)

        # Verify item has been created
        resp = self.app.get("/v1/keys/test_new_key_1?scope=st2kv.user&user=user2")
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(resp.json["value"], "testvalue1")
        self.assertEqual(resp.json["scope"], FULL_USER_SCOPE)
        self.assertEqual(resp.json["user"], "user2")

    def test_set_user_scoped_item_arbitrary_user_non_admin_failure(self):
        user_6_db = UserDB(name="user6")
        user_6_db = User.add_or_update(user_6_db)
        self.users["user_6"] = user_6_db

        # set permission type for user
        grant_7_db = PermissionGrantDB(
            resource_uid="key_value_pair:st2kv.user:user6:test_new_key_3",
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_SET],
        )
        grant_7_db = PermissionGrant.add_or_update(grant_7_db)
        grant_8_db = PermissionGrantDB(
            resource_uid="key_value_pair:st2kv.user:user6:test_new_key_3",
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_VIEW],
        )
        grant_8_db = PermissionGrant.add_or_update(grant_8_db)
        permission_grants = [str(grant_7_db.id), str(grant_8_db.id)]
        role_1_db = RoleDB(name="user6", permission_grants=permission_grants)
        role_1_db = Role.add_or_update(role_1_db)
        self.roles["user_6"] = role_1_db

        user_db = self.users["user_6"]
        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=self.roles["user_6"].name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        # Non admin user can't set user scoped item for arbitrary user but just for themselves
        self.use_user(self.users["user_6"])

        data = {
            "name": "test_new_key_2",
            "value": "testvalue2",
            "scope": FULL_USER_SCOPE,
            "user": "user2",
        }
        resp = self.app.put_json("/v1/keys/test_new_key_2", data, expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)
        self.assertTrue(
            '"user" attribute can only be provided by admins'
            in resp.json["faultstring"]
        )

        # But setting user scoped item for themselves should work
        data = {
            "name": "test_new_key_3",
            "value": "testvalue3",
            "scope": FULL_USER_SCOPE,
        }
        resp = self.app.put_json("/v1/keys/test_new_key_3", data)
        self.assertEqual(resp.status_code, http_client.OK)

        resp = self.app.get("/v1/keys/test_new_key_3?scope=st2kv.user")
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(resp.json["value"], "testvalue3")
        self.assertEqual(resp.json["scope"], FULL_USER_SCOPE)
        self.assertEqual(resp.json["user"], "user6")

    def test_delete_system_scoped_item_non_admin_success(self):
        # Non-admin user can delete any system-scoped item
        self.use_user(self.users["user_1"])

        resp = self.app.get("/v1/keys/%s" % (self.kvps["kvp_1"].name))
        self.assertEqual(resp.status_code, http_client.OK)

        resp = self.app.delete("/v1/keys/%s" % (self.kvps["kvp_1"].name))
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        # Verify it has been deleted
        resp = self.app.get(
            "/v1/keys/%s" % (self.kvps["kvp_1"].name), expect_errors=True
        )
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)

    def test_delete_user_scoped_item_non_admin_scoped_to_itself_success(self):
        user_5_db = UserDB(name="user5")
        user_5_db = User.add_or_update(user_5_db)
        self.users["user_5"] = user_5_db

        grant_5_db = PermissionGrantDB(
            resource_uid="key_value_pair:st2kv.user:user5:test_user_scope_1",
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_VIEW],
        )
        grant_5_db = PermissionGrant.add_or_update(grant_5_db)
        grant_6_db = PermissionGrantDB(
            resource_uid="key_value_pair:st2kv.user:user5:test_user_scope_8",
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_DELETE],
        )
        grant_6_db = PermissionGrant.add_or_update(grant_6_db)
        permission_grants = [str(grant_5_db.id), str(grant_6_db.id)]
        role_2_db = RoleDB(name="user5", permission_grants=permission_grants)
        role_2_db = Role.add_or_update(role_2_db)
        self.roles["user_5"] = role_2_db

        user_db = self.users["user_5"]
        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=self.roles["user_5"].name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        # Non-admin user can delete user scoped item scoped to themselves
        self.use_user(self.users["user_5"])

        resp = self.app.get("/v1/keys/%s?scope=st2kv.user" % (self.kvps["kvp_7"].name))
        self.assertEqual(resp.status_code, http_client.OK)

        resp = self.app.delete(
            "/v1/keys/%s?scope=st2kv.user" % (self.kvps["kvp_8"].name)
        )
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        # But unable to delete item scoped to other user (user2)
        resp = self.app.delete(
            "/v1/keys/%s?scope=st2kv.user" % (self.kvps["kvp_8"].name),
            expect_errors=True,
        )
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)

    def test_delete_user_scope_item_aribrary_user_admin_success(self):
        # Admin user can delete user-scoped datastore item scoped to arbitrary user
        self.use_user(self.users["admin"])

        resp = self.app.get(
            "/v1/keys/%s?scope=st2kv.user&user=user1" % (self.kvps["kvp_3"].name)
        )
        self.assertEqual(resp.status_code, http_client.OK)
        resp = self.app.get(
            "/v1/keys/%s?scope=st2kv.user&user=user2" % (self.kvps["kvp_5"].name)
        )
        self.assertEqual(resp.status_code, http_client.OK)

        resp = self.app.delete(
            "/v1/keys/%s?scope=st2kv.user&user=user1" % (self.kvps["kvp_3"].name)
        )
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)
        resp = self.app.delete(
            "/v1/keys/%s?scope=st2kv.user&user=user2" % (self.kvps["kvp_5"].name)
        )
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        resp = self.app.delete(
            "/v1/keys/%s?scope=st2kv.user&user=user1" % (self.kvps["kvp_3"].name),
            expect_errors=True,
        )
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        resp = self.app.delete(
            "/v1/keys/%s?scope=st2kv.user&user=user2" % (self.kvps["kvp_5"].name),
            expect_errors=True,
        )

    def test_delete_user_scope_item_non_admin_failure(self):
        # Non admin user can't delete user-scoped items which are not scoped to them
        self.use_user(self.users["user_1"])

        resp = self.app.get(
            "/v1/keys/%s?scope=st2kv.user&user=user2" % (self.kvps["kvp_5"].name),
            expect_errors=True,
        )
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)
        self.assertTrue(
            '"user" attribute can only be provided by admins'
            in resp.json["faultstring"]
        )

    def test_get_all_limit_minus_one(self):
        user_db = self.users["observer"]
        self.use_user(user_db)

        resp = self.app.get("/v1/keys?limit=-1", expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

        user_db = self.users["admin"]
        self.use_user(user_db)

        resp = self.app.get("/v1/keys?limit=-1")
        self.assertEqual(resp.status_code, http_client.OK)
