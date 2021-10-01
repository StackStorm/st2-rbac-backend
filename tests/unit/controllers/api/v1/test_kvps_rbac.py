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

from st2common.constants.keyvalue import FULL_SYSTEM_SCOPE, FULL_USER_SCOPE
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
from st2common import log as logging

from tests.base import APIControllerWithRBACTestCase

LOG = logging.getLogger(__name__)

http_client = six.moves.http_client

__all__ = [
    "KeyValuesControllerRBACTestCase",
    "KeyValueSystemScopeControllerRBACTestCase",
    "KeyValueUserScopeControllerRBACTestCase",
]


class KeyValuesControllerRBACTestCase(APIControllerWithRBACTestCase):
    @classmethod
    def setUpClass(cls):
        super(KeyValuesControllerRBACTestCase, cls).setUpClass()


class KeyValueSystemScopeControllerRBACTestCase(KeyValuesControllerRBACTestCase):
    def setUp(self):
        super(KeyValueSystemScopeControllerRBACTestCase, self).setUp()

        self.kvps = {}

        # Insert mock kvp objects
        kvp_1_api = KeyValuePairSetAPI(
            name="key1", value="val1", scope=FULL_SYSTEM_SCOPE
        )
        kvp_1_db = KeyValuePairSetAPI.to_model(kvp_1_api)
        kvp_1_db = KeyValuePair.add_or_update(kvp_1_db)
        kvp_1_db = KeyValuePairAPI.from_model(kvp_1_db)
        self.kvps["kvp_1_api"] = kvp_1_db

        kvp_2_api = KeyValuePairSetAPI(
            name="key2", value="val2", scope=FULL_SYSTEM_SCOPE
        )
        kvp_2_db = KeyValuePairSetAPI.to_model(kvp_2_api)
        kvp_2_db = KeyValuePair.add_or_update(kvp_2_db)
        kvp_2_db = KeyValuePairAPI.from_model(kvp_2_db)
        self.kvps["kvp_2_api"] = kvp_2_db

    def test_admin_for_system_scope_kvps(self):
        # Admin user should have general list permissions on system kvps.
        self.use_user(self.users["admin"])

        resp = self.app.get("/v1/keys?limit=-1")
        self.assertEqual(resp.status_int, 200)

        resp = self.app.get("/v1/keys/")
        self.assertEqual(resp.status_int, 200)
        for item in resp.json:
            self.assertEqual(item["scope"], FULL_SYSTEM_SCOPE)

        # Admin user should have all permission on the system kvps
        for k in ["key1", "key2"]:
            resp = self.app.get("/v1/keys/%s" % (k))
            self.assertEqual(resp.status_int, 200)

            data1 = {
                "name": "key1",
                "value": "val1",
                "scope": FULL_SYSTEM_SCOPE,
            }
            resp = self.app.put_json("/v1/keys/key1", data1, expect_errors=True)
            self.assertEqual(resp.status_int, 200)

            resp = self.app.get("/v1/keys/%s?scope=st2kv.system" % (k))
            self.assertEqual(resp.status_int, 200)

            resp = self.app.delete("/v1/keys/%s" % (k))
            self.assertEqual(resp.status_code, http_client.NO_CONTENT)

    def test_observer_for_system_scope_kvps(self):
        # Observer user should have general list permissions on system kvps.
        self.use_user(self.users["observer"])
        resp = self.app.get("/v1/keys?limit=-1", expect_errors=True)
        self.assertEqual(resp.status_int, 200)

        resp = self.app.get("/v1/keys/")
        self.assertEqual(resp.status_int, 200)
        for item in resp.json:
            self.assertEqual(item["scope"], FULL_SYSTEM_SCOPE)

        # Observer user should have read permissions on the system kvps
        for k in ["key1", "key2"]:
            resp = self.app.get("/v1/keys/%s" % (k))
            self.assertEqual(resp.status_int, 200)

            resp = self.app.get("/v1/keys/%s?scope=st2kv.system" % (k))
            self.assertEqual(resp.status_int, 200)

            data1 = {
                "name": "key1",
                "value": "val1",
                "scope": FULL_SYSTEM_SCOPE,
            }
            resp = self.app.put_json("/v1/keys/key1", data1, expect_errors=True)
            self.assertEqual(resp.status_code, http_client.FORBIDDEN)

            resp = self.app.delete("/v1/keys/%s" % (k), expect_errors=True)
            self.assertEqual(resp.status_code, http_client.FORBIDDEN)

    def test_user_default_for_system_scope_kvps(self):
        user_1_db = UserDB(name="no_roles")
        user_1_db = User.add_or_update(user_1_db)
        self.users[user_1_db.name] = user_1_db

        user_2_db = UserDB(name="1_custom_role_no_permissions")
        user_2_db = User.add_or_update(user_2_db)
        self.users[user_2_db.name] = user_2_db

        self.use_user(self.users["no_roles"])
        # User with no roles should not have any permission on the system kvp
        resp = self.app.get(
            "/v1/keys/%s" % (self.kvps["kvp_1_api"].name), expect_errors=True
        )
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)
        resp = self.app.get(
            "/v1/keys/%s" % (self.kvps["kvp_2_api"].name), expect_errors=True
        )
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

        self.use_user(self.users["1_custom_role_no_permissions"])
        # User with no roles should not have any permission on the system kvp
        resp = self.app.get(
            "/v1/keys/%s" % (self.kvps["kvp_1_api"].name), expect_errors=True
        )
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)
        resp = self.app.get(
            "/v1/keys/%s" % (self.kvps["kvp_2_api"].name), expect_errors=True
        )
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

    def test_get_one_system_scope(self):

        kvp_1_uid = "%s:%s:key1" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE)

        # Setup user, grant, role, and assignment records
        user_db = UserDB(name="system_key1_read")
        user_db = User.add_or_update(user_db)
        self.users[user_db.name] = user_db

        grant_db = PermissionGrantDB(
            resource_uid=kvp_1_uid,
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[
                PermissionType.KEY_VALUE_PAIR_LIST,
                PermissionType.KEY_VALUE_PAIR_VIEW,
            ],
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

        self.use_user(self.users["system_key1_read"])

        # User should have read but no write permissions on system kvp key1.
        resp = self.app.get("/v1/keys/key1")
        self.assertEqual(resp.status_int, 200)

        data = {
            "name": "key1",
            "value": "val1",
            "scope": FULL_SYSTEM_SCOPE,
        }
        resp = self.app.put_json(
            "/v1/keys/key1?scope=st2kv.system", data, expect_errors=True
        )
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

        resp = self.app.delete("/v1/keys/key1?scope=st2kv.system", expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

    def test_get_all_scope_system_decrypt_admin(self):
        # Admin should be able to view all system scoped decrypted values
        self.use_user(self.users["admin"])

        resp = self.app.get("/v1/keys?decrypt=True")
        self.assertEqual(resp.status_int, 200)
        for item in resp.json:
            self.assertEqual(item["scope"], FULL_SYSTEM_SCOPE)

        resp = self.app.get("/v1/keys?scope=all&decrypt=True")
        self.assertEqual(resp.status_int, 200)
        for item in resp.json:
            self.assertEqual(item["scope"], FULL_SYSTEM_SCOPE)

    def test_get_all_non_admin_decrypt(self):
        user_1_db = UserDB(name="user_decrypt_all")
        user_1_db = User.add_or_update(user_1_db)
        self.users[user_1_db.name] = user_1_db
        # Non admin shouldn't be able to view decrypted items
        self.use_user(self.users["user_decrypt_all"])

        resp = self.app.get("/v1/keys?decrypt=True", expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)
        self.assertTrue(
            "Decrypt option requires administrator access" in resp.json["faultstring"]
        )

    def test_user_custom_set_for_system_scope_kvps(self):
        kvp_1_uid = "%s:%s:test_new_key_3" % (
            ResourceType.KEY_VALUE_PAIR,
            FULL_SYSTEM_SCOPE,
        )
        # setup user
        user_9_db = UserDB(name="user9")
        user_9_db = User.add_or_update(user_9_db)
        self.users["user_9"] = user_9_db

        # set permission type for user
        grant_7_db = PermissionGrantDB(
            resource_uid=kvp_1_uid,
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[
                PermissionType.KEY_VALUE_PAIR_SET,
                PermissionType.KEY_VALUE_PAIR_VIEW,
                PermissionType.KEY_VALUE_PAIR_LIST,
            ],
        )
        grant_7_db = PermissionGrant.add_or_update(grant_7_db)

        permission_grants = [str(grant_7_db.id)]
        role_1_db = RoleDB(name="user9", permission_grants=permission_grants)
        role_1_db = Role.add_or_update(role_1_db)
        self.roles["user_9"] = role_1_db

        user_db = self.users["user_9"]
        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=self.roles["user_9"].name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        self.use_user(self.users["user_9"])
        # User should have read and set but no delete permissions on system kvp key1.
        data = {
            "name": "test_new_key_3",
            "value": "testvalue3",
            "scope": FULL_SYSTEM_SCOPE,
        }
        resp = self.app.put_json("/v1/keys/test_new_key_3?scope=st2kv.system", data)
        self.assertEqual(resp.status_code, http_client.OK)

        resp = self.app.get("/v1/keys/test_new_key_3")
        self.assertEqual(resp.status_int, 200)

        resp = self.app.get("/v1/keys/")
        self.assertEqual(resp.status_int, 200)

        resp = self.app.delete(
            "/v1/keys/test_new_key_3?scope=st2kv.system", expect_errors=True
        )
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

        data = {
            "name": "test_new_key_4",
            "value": "testvalue4",
            "scope": FULL_SYSTEM_SCOPE,
        }
        resp = self.app.put_json(
            "/v1/keys/test_new_key_4?scope=system", data, expect_errors=True
        )
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

    def test_user_custom_delete_for_system_scope_kvps(self):
        kvp_1_uid = "%s:%s:key1" % (
            ResourceType.KEY_VALUE_PAIR,
            FULL_SYSTEM_SCOPE,
        )
        # setup user
        user_9_db = UserDB(name="user9")
        user_9_db = User.add_or_update(user_9_db)
        self.users["user_9"] = user_9_db

        # set permission type for user
        grant_7_db = PermissionGrantDB(
            resource_uid=kvp_1_uid,
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[
                PermissionType.KEY_VALUE_PAIR_SET,
                PermissionType.KEY_VALUE_PAIR_VIEW,
                PermissionType.KEY_VALUE_PAIR_DELETE,
            ],
        )
        grant_7_db = PermissionGrant.add_or_update(grant_7_db)

        permission_grants = [str(grant_7_db.id)]
        role_1_db = RoleDB(name="user9", permission_grants=permission_grants)
        role_1_db = Role.add_or_update(role_1_db)
        self.roles["user_9"] = role_1_db

        user_db = self.users["user_9"]
        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=self.roles["user_9"].name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        self.use_user(self.users["user_9"])

        data = {
            "name": "test_new_key_4",
            "value": "testvalue4",
            "scope": FULL_SYSTEM_SCOPE,
        }
        resp = self.app.put_json(
            "/v1/keys/test_new_key_4?scope=st2kv.system", data, expect_errors=True
        )
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

        resp = self.app.get("/v1/keys/%s" % (self.kvps["kvp_1_api"].name))
        self.assertEqual(resp.status_int, 200)

        resp = self.app.delete(
            "/v1/keys/%s?scope=st2kv.system" % (self.kvps["kvp_1_api"].name)
        )
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        resp = self.app.delete(
            "/v1/keys/test_new_key_3?scope=st2kv.system", expect_errors=True
        )
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

    def test_user_custom_all_for_system_scope_kvps(self):
        kvp_1_uid = "%s:%s:test_new_key_3" % (
            ResourceType.KEY_VALUE_PAIR,
            FULL_SYSTEM_SCOPE,
        )
        # setup user
        user_9_db = UserDB(name="user9")
        user_9_db = User.add_or_update(user_9_db)
        self.users["user_9"] = user_9_db

        # set permission type for user
        grant_7_db = PermissionGrantDB(
            resource_uid=kvp_1_uid,
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_PAIR_ALL],
        )
        grant_7_db = PermissionGrant.add_or_update(grant_7_db)

        permission_grants = [str(grant_7_db.id)]
        role_1_db = RoleDB(name="user9", permission_grants=permission_grants)
        role_1_db = Role.add_or_update(role_1_db)
        self.roles["user_9"] = role_1_db

        user_db = self.users["user_9"]
        role_assignment_db = UserRoleAssignmentDB(
            user=user_db.name,
            role=self.roles["user_9"].name,
            source="assignments/%s.yaml" % user_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        self.use_user(self.users["user_9"])

        data = {
            "name": "test_new_key_3",
            "value": "testvalue2",
            "scope": FULL_SYSTEM_SCOPE,
        }
        resp = self.app.put_json("/v1/keys/test_new_key_3?scope=st2kv.system", data)
        self.assertEqual(resp.status_code, http_client.OK)

        resp = self.app.get("/v1/keys/test_new_key_3")
        self.assertEqual(resp.status_code, http_client.OK)

        resp = self.app.delete("/v1/keys/test_new_key_3?scope=st2kv.system")
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)


class KeyValueUserScopeControllerRBACTestCase(KeyValuesControllerRBACTestCase):
    def test_user_for_user_scope_kvps(self):
        # Setup users. No explicit grant, role, and assignment records should be
        # required for user to access their KVPs
        user_1_db = UserDB(name="user101")
        user_1_db = User.add_or_update(user_1_db)
        self.users[user_1_db.name] = user_1_db

        user_2_db = UserDB(name="user102")
        user_2_db = User.add_or_update(user_2_db)
        self.users[user_2_db.name] = user_2_db

        self.kvps = {}
        self.use_user(self.users["user101"])

        # Insert user scoped key value pairs for user1.
        name = get_key_reference(scope=FULL_USER_SCOPE, name="mykey1", user="myval1")
        kvp_db = KeyValuePairDB(name=name, value="myval1", scope=FULL_USER_SCOPE)
        kvp_db = KeyValuePair.add_or_update(kvp_db)
        kvp_db = KeyValuePairAPI.from_model(kvp_db)
        self.kvps["kvp_3_api"] = kvp_db

        name = get_key_reference(scope=FULL_USER_SCOPE, name="mykey2", user="myval2")
        kvp_db = KeyValuePairDB(name=name, value="myval2", scope=FULL_USER_SCOPE)
        kvp_db = KeyValuePair.add_or_update(kvp_db)
        kvp_db = KeyValuePairAPI.from_model(kvp_db)
        self.kvps["kvp_4_api"] = kvp_db

        # User1 should have general list permissions on user1's kvps.
        resp = self.app.get("/v1/keys?scope=st2kv.user")
        self.assertEqual(resp.status_int, 200)
        for item in resp.json:
            self.assertEqual(item["scope"], FULL_USER_SCOPE)
            self.assertEqual(item["user"], "user101")

        # User1 should have all permission on the user1's kvps
        data1 = {
            "name": "mykey1",
            "value": "myval1",
            "scope": FULL_USER_SCOPE,
            "user": "user101",
        }
        resp = self.app.put_json("/v1/keys/mykey1?scope=st2kv.user", data1)
        self.assertEqual(resp.status_int, 200)

        resp = self.app.get(
            "/v1/keys/%s?scope=st2kv.user" % (self.kvps["kvp_3_api"].name)
        )
        self.assertEqual(resp.status_int, 200)

        resp = self.app.delete(
            "/v1/keys/%s?scope=st2kv.user" % (self.kvps["kvp_3_api"].name)
        )
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        data2 = {
            "name": "mykey2",
            "value": "myval2",
            "scope": FULL_USER_SCOPE,
            "user": "user101",
        }
        resp = self.app.put_json("/v1/keys/mykey2?scope=st2kv.user", data2)
        self.assertEqual(resp.status_int, 200)

        resp = self.app.get(
            "/v1/keys/%s?scope=st2kv.user" % (self.kvps["kvp_4_api"].name)
        )
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.json["scope"], FULL_USER_SCOPE)
        self.assertEqual(resp.json["user"], "user101")

        resp = self.app.delete(
            "/v1/keys/%s?scope=st2kv.user" % (self.kvps["kvp_4_api"].name)
        )
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        # User2 should not have any permissions on user1's kvps.
        self.use_user(self.users["user102"])

        data1 = {
            "name": "mykey1",
            "value": "myval1",
            "scope": FULL_USER_SCOPE,
            "user": "user101",
        }
        resp = self.app.put_json(
            "/v1/keys/mykey1?scope=st2kv.user", data1, expect_errors=True
        )
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

    def test_user_for_another_user_kvps(self):
        kvp_4_uid = "%s:%s:mykey3" % (ResourceType.KEY_VALUE_PAIR, FULL_USER_SCOPE)

        # Setup users. No explicit grant, role, and assignment records should be
        # required for user to access their KVPs
        user_1_db = UserDB(name="user103")
        user_1_db = User.add_or_update(user_1_db)
        self.users[user_1_db.name] = user_1_db

        user_2_db = UserDB(name="user104")
        user_2_db = User.add_or_update(user_2_db)
        self.users[user_2_db.name] = user_2_db

        self.kvps = {}

        # Insert user scoped key value pairs for user1.
        name = get_key_reference(scope=FULL_USER_SCOPE, name="mykey3", user="myval3")
        kvp_db = KeyValuePairDB(name=name, value="myval3", scope=FULL_USER_SCOPE)
        kvp_db = KeyValuePair.add_or_update(kvp_db)
        kvp_db = KeyValuePairAPI.from_model(kvp_db)
        self.kvps["kvp_4_api"] = kvp_db

        # role assignment
        grant_db = PermissionGrantDB(
            resource_uid=kvp_4_uid,
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_PAIR_ALL],
        )
        grant_db = PermissionGrant.add_or_update(grant_db)

        role_db = RoleDB(
            name="custom_role_system_key3_all_grant",
            permission_grants=[str(grant_db.id)],
        )
        role_db = Role.add_or_update(role_db)
        self.roles[role_db.name] = role_db

        role_assignment_db = UserRoleAssignmentDB(
            user=user_1_db.name,
            role=role_db.name,
            source="assignments/%s.yaml" % user_1_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)

        self.use_user(self.users["user104"])

        # User2 should not have any permissions on user1's kvps.
        data1 = {
            "name": "mykey3",
            "value": "myval3",
            "scope": FULL_USER_SCOPE,
            "user": "user103",
        }
        resp = self.app.put_json(
            "/v1/keys/mykey3?scope=st2kv.user", data1, expect_errors=True
        )
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

        resp = self.app.get("/v1/keys/mykey3", expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

        resp = self.app.delete("/v1/keys/mykey3", expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

        resp = self.app.get(
            "/v1/keys/%s?scope=st2kv.user&user=user103" % (self.kvps["kvp_4_api"].name),
            expect_errors=True,
        )
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)
        self.assertTrue(
            '"user" attribute can only be provided by admins'
            in resp.json["faultstring"]
        )

    def test_get_one_user_scope_decrypt(self):
        self.kvps = {}
        kvp_4_uid = "%s:%s:test_user_scope_5" % (
            ResourceType.KEY_VALUE_PAIR,
            FULL_SYSTEM_SCOPE,
        )

        user_1_db = UserDB(name="user105")
        user_1_db = User.add_or_update(user_1_db)
        self.users[user_1_db.name] = user_1_db
        name = get_key_reference(
            scope=FULL_USER_SCOPE, name="test_user_scope_5", user="user105"
        )
        kvp_api = KeyValuePairSetAPI(
            name=name, value="user_secret", scope=FULL_USER_SCOPE, secret=True
        )
        kvp_db = KeyValuePairSetAPI.to_model(kvp_api)
        kvp_db = KeyValuePair.add_or_update(kvp_db)
        kvp_db = KeyValuePairAPI.from_model(kvp_db)
        self.kvps["kvp_6_api"] = kvp_db

        # role assignment
        grant_db = PermissionGrantDB(
            resource_uid=kvp_4_uid,
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_PAIR_VIEW],
        )
        grant_db = PermissionGrant.add_or_update(grant_db)

        role_db = RoleDB(
            name="custom_role_system_key3_view_grant",
            permission_grants=[str(grant_db.id)],
        )
        role_db = Role.add_or_update(role_db)
        self.roles[role_db.name] = role_db
        role_assignment_db = UserRoleAssignmentDB(
            user=user_1_db.name,
            role=role_db.name,
            source="assignments/%s.yaml" % user_1_db.name,
        )
        UserRoleAssignment.add_or_update(role_assignment_db)
        # User can request decrypted value of the item scoped to themselves
        self.use_user(self.users["user105"])
        resp = self.app.get(
            "/v1/keys/%s?scope=st2kv.user&decrypt=True" % (self.kvps["kvp_6_api"].name)
        )
        self.assertEqual(resp.json["scope"], FULL_USER_SCOPE)
        self.assertEqual(resp.json["user"], "user105")
        self.assertTrue(resp.json["secret"])
        self.assertEqual(resp.json["value"], "user_secret")

        # Non-admin user can't access decrypted system scoped items. They can only access decrypted
        # items which are scoped to themselves.
        resp = self.app.get("/v1/keys?decrypt=True", expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)
        self.assertTrue(
            "Decrypt option requires administrator access" in resp.json["faultstring"]
        )

    def test_admin_for_user_scope_kvps(self):
        # Admin user can delete user-scoped datastore item scoped to arbitrary user
        self.use_user(self.users["admin"])

        self.kvps = {}
        user_1_db = UserDB(name="user106")
        user_1_db = User.add_or_update(user_1_db)
        self.users[user_1_db.name] = user_1_db

        user_1_db = UserDB(name="user107")
        user_1_db = User.add_or_update(user_1_db)
        self.users[user_1_db.name] = user_1_db

        name = get_key_reference(
            scope=FULL_USER_SCOPE, name="test_user_scope_5", user="user106"
        )
        kvp_api = KeyValuePairSetAPI(
            name=name, value="user_secret", scope=FULL_USER_SCOPE, secret=True
        )
        kvp_db = KeyValuePairSetAPI.to_model(kvp_api)
        kvp_db = KeyValuePair.add_or_update(kvp_db)
        kvp_db = KeyValuePairAPI.from_model(kvp_db)
        self.kvps["kvp_6_api"] = kvp_db

        name = get_key_reference(
            scope=FULL_USER_SCOPE, name="test_user_scope_6", user="user107"
        )
        kvp_api = KeyValuePairSetAPI(
            name=name, value="user_secret", scope=FULL_USER_SCOPE, secret=True
        )
        kvp_db = KeyValuePairSetAPI.to_model(kvp_api)
        kvp_db = KeyValuePair.add_or_update(kvp_db)
        kvp_db = KeyValuePairAPI.from_model(kvp_db)
        self.kvps["kvp_7_api"] = kvp_db

        self.use_user(self.users["user106"])
        data1 = {
            "name": "test_user_scope_5",
            "value": "user_secret",
            "scope": FULL_USER_SCOPE,
            "user": "user106",
        }
        resp = self.app.put_json("/v1/keys/test_user_scope_5?scope=st2kv.user", data1)
        self.assertEqual(resp.status_int, 200)
        resp = self.app.get(
            "/v1/keys/%s?scope=st2kv.user" % (self.kvps["kvp_6_api"].name)
        )
        self.assertEqual(resp.status_code, http_client.OK)
        resp = self.app.delete(
            "/v1/keys/%s?scope=st2kv.user" % (self.kvps["kvp_6_api"].name)
        )
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        self.use_user(self.users["user107"])
        data2 = {
            "name": "test_user_scope_6",
            "value": "user_secret",
            "scope": FULL_USER_SCOPE,
            "user": "user107",
        }
        resp = self.app.put_json("/v1/keys/test_user_scope_6?scope=st2kv.user", data2)
        self.assertEqual(resp.status_int, 200)
        resp = self.app.get(
            "/v1/keys/%s?scope=st2kv.user" % (self.kvps["kvp_7_api"].name)
        )
        self.assertEqual(resp.status_code, http_client.OK)
        resp = self.app.delete(
            "/v1/keys/%s?scope=st2kv.user" % (self.kvps["kvp_7_api"].name),
            expect_errors=True,
        )
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

    def test_user_set_user_scope(self):

        kvp_1_uid = "%s:%s:test_new_key_3" % (
            ResourceType.KEY_VALUE_PAIR,
            FULL_USER_SCOPE,
        )

        # setup user
        user_6_db = UserDB(name="user6")
        user_6_db = User.add_or_update(user_6_db)
        self.users["user_6"] = user_6_db

        # set permission type for user
        grant_7_db = PermissionGrantDB(
            resource_uid=kvp_1_uid,
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_PAIR_SET],
        )
        grant_7_db = PermissionGrant.add_or_update(grant_7_db)
        grant_8_db = PermissionGrantDB(
            resource_uid=kvp_1_uid,
            resource_type=ResourceType.KEY_VALUE_PAIR,
            permission_types=[PermissionType.KEY_VALUE_PAIR_VIEW],
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
