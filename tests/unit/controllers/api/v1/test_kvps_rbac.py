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
        cls.resources = {}

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


class KeyValueSystemScopeControllerRBACTestCase(KeyValuesControllerRBACTestCase):
    def setUp(self):
        super(KeyValueSystemScopeControllerRBACTestCase, self).setUp()

        # Insert system scoped key value pairs.
        kvp_1_api = KeyValuePairSetAPI(
            uid="%s:%s:key1" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE),
            scope=FULL_SYSTEM_SCOPE,
            name="key1",
            value="val1",
            secret=True,
        )
        kvp_1_db = KeyValuePairSetAPI.to_model(kvp_1_api)
        kvp_1_db = KeyValuePair.add_or_update(kvp_1_db)
        self.resources[kvp_1_db.uid] = kvp_1_db

        kvp_2_api = KeyValuePairSetAPI(
            uid="%s:%s:key2" % (ResourceType.KEY_VALUE_PAIR, FULL_SYSTEM_SCOPE),
            scope=FULL_SYSTEM_SCOPE,
            name="key2",
            value="val2",
            secret=True,
        )
        kvp_2_db = KeyValuePairSetAPI.to_model(kvp_2_api)
        kvp_2_db = KeyValuePair.add_or_update(kvp_2_db)
        self.resources[kvp_2_db.uid] = kvp_2_db

        # Setup users for user scoped KVPs.
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

    def test_admin_permissions_for_system_scope_kvps(self):
        # Set context to user
        self.use_user(self.users["admin"])

        # Admin should have general list permissions on system kvps.
        resp = self.app.get("/v1/keys?limit=-1")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 2)
        self.assertTrue(all([item["scope"] == FULL_SYSTEM_SCOPE for item in resp.json]))
        self.assertTrue(all([len(item["value"]) > 10 for item in resp.json]))

        resp = self.app.get("/v1/keys?limit=-1&decrypt=True")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 2)
        self.assertTrue(all([item["scope"] == FULL_SYSTEM_SCOPE for item in resp.json]))
        self.assertListEqual([item["value"] for item in resp.json], ["val1", "val2"])

        resp = self.app.get("/v1/keys/")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 2)
        self.assertTrue(all([item["scope"] == FULL_SYSTEM_SCOPE for item in resp.json]))

        resp = self.app.get("/v1/keys?scope=all")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 2)
        self.assertTrue(all([item["scope"] == FULL_SYSTEM_SCOPE for item in resp.json]))

        resp = self.app.get("/v1/keys?scope=system")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 2)
        self.assertTrue(all([item["scope"] == FULL_SYSTEM_SCOPE for item in resp.json]))

        resp = self.app.get("/v1/keys?scope=user")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 0)

        # Admin should have all permission on the system kvps
        for i in range(1, 3):
            k, v = "key" + str(i), "val" + str(i)

            # view permission
            resp = self.app.get("/v1/keys/%s?decrypt=True" % k)
            self.assertEqual(resp.status_int, http_client.OK)
            self.assertEqual(resp.json["value"], v)

            # set permission
            d = {
                "name": k,
                "value": "value for %s" % k,
                "scope": FULL_SYSTEM_SCOPE,
                "secret": True,
            }
            resp = self.app.put_json("/v1/keys/%s" % k, d)
            self.assertEqual(resp.status_int, http_client.OK)

            resp = self.app.get("/v1/keys/%s?decrypt=True&scope=st2kv.system" % k)
            self.assertEqual(resp.status_int, http_client.OK)
            self.assertEqual(resp.json["value"], "value for %s" % k)

            # delete permission
            resp = self.app.delete("/v1/keys/%s" % k)
            self.assertEqual(resp.status_code, http_client.NO_CONTENT)

            resp = self.app.get("/v1/keys/%s?scope=st2kv.system" % k, expect_errors=True)
            self.assertEqual(resp.status_int, http_client.NOT_FOUND)

    def test_observer_permissions_for_system_scope_kvps(self):
        # Set context to user
        self.use_user(self.users["observer"])

        # Observer does not have limit=-1 list permissions on system kvps.
        resp = self.app.get("/v1/keys?limit=-1", expect_errors=True)
        self.assertEqual(resp.status_int, http_client.FORBIDDEN)

        # Observer does not have decrypt permission on system kvps.
        resp = self.app.get("/v1/keys?decrypt=True", expect_errors=True)
        self.assertEqual(resp.status_int, http_client.FORBIDDEN)

        # Observer should have general list permissions on system kvps.
        resp = self.app.get("/v1/keys/")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 2)
        self.assertTrue(all([item["scope"] == FULL_SYSTEM_SCOPE for item in resp.json]))
        self.assertTrue(all([len(item["value"]) > 10 for item in resp.json]))

        resp = self.app.get("/v1/keys?scope=all")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 2)
        self.assertTrue(all([item["scope"] == FULL_SYSTEM_SCOPE for item in resp.json]))

        resp = self.app.get("/v1/keys?scope=system")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 2)
        self.assertTrue(all([item["scope"] == FULL_SYSTEM_SCOPE for item in resp.json]))

        resp = self.app.get("/v1/keys?scope=user")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 0)

        # Observer should have read but not write permission on the system kvps
        for i in range(1, 3):
            k, v = "key" + str(i), "val" + str(i)

            # view permission
            resp = self.app.get("/v1/keys/%s?decrypt=True" % k)
            self.assertEqual(resp.status_int, http_client.OK)
            self.assertEqual(resp.json["value"], v)

            # set permission
            d = {
                "name": k,
                "value": "value for %s" % k,
                "scope": FULL_SYSTEM_SCOPE,
                "secret": True,
            }
            resp = self.app.put_json("/v1/keys/%s" % k, d, expect_errors=True)
            self.assertEqual(resp.status_int, http_client.FORBIDDEN)

            resp = self.app.get("/v1/keys/%s?decrypt=True&scope=st2kv.system" % k)
            self.assertEqual(resp.status_int, http_client.OK)
            self.assertEqual(resp.json["value"], v)

            # delete permission
            resp = self.app.delete("/v1/keys/%s" % k, expect_errors=True)
            self.assertEqual(resp.status_code, http_client.FORBIDDEN)

            resp = self.app.get("/v1/keys/%s?decrypt=True&scope=st2kv.system" % k)
            self.assertEqual(resp.status_int, http_client.OK)

    def test_user_default_permissions_for_system_scope_kvps(self):
        # Set context to user
        self.use_user(self.users["no_permissions"])

        # User does not have limit=-1 list permissions on kvps.
        resp = self.app.get("/v1/keys?limit=-1")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 0)

        # User does not have general list permissions on system kvps so result is empty.
        resp = self.app.get("/v1/keys/")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 0)

        resp = self.app.get("/v1/keys?scope=all")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 0)

        resp = self.app.get("/v1/keys?scope=system")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 0)

        resp = self.app.get("/v1/keys?scope=user")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 0)

        # User should not have read and write permission on the system kvps
        for i in range(1, 3):
            k = "key" + str(i)

            # view permission
            resp = self.app.get("/v1/keys/%s?scope=system" % k, expect_errors=True)
            self.assertEqual(resp.status_int, http_client.FORBIDDEN)

            # set permission
            d = {
                "name": k,
                "value": "value for %s" % k,
                "scope": FULL_SYSTEM_SCOPE,
            }
            resp = self.app.put_json("/v1/keys/%s?scope=system" % k, d, expect_errors=True)
            self.assertEqual(resp.status_int, http_client.FORBIDDEN)

            # delete permission
            resp = self.app.delete("/v1/keys/%s?scope=system" % k, expect_errors=True)
            self.assertEqual(resp.status_code, http_client.FORBIDDEN)

    def test_user_custom_read_permissions_for_system_scope_kvps(self):
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

        # Set context to user
        self.use_user(self.users[user_db.name])

        # User should be able to list the system and user scoped kvps that user has permission to.
        resp = self.app.get("/v1/keys/")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]["name"], "key1")
        self.assertEqual(resp.json[0]["scope"], FULL_SYSTEM_SCOPE)

        # User should have read but no write permissions on system kvp key1.
        k, v = kvp_1_db.name, "val1"
        resp = self.app.get("/v1/keys/%s?decrypt=True&scope=system" % k)
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(resp.json["value"], v)

        d = {
            "name": k,
            "value": "value for %s" % k,
            "scope": FULL_SYSTEM_SCOPE,
        }
        resp = self.app.put_json("/v1/keys/%s?scope=system" % k, d, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.FORBIDDEN)

        resp = self.app.delete("/v1/keys/%s?scope=system" % k, expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

        # User should not have read and write permissions on system kvp key2.
        k = kvp_2_db.name
        resp = self.app.get("/v1/keys/%s?scope=system" % k, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.FORBIDDEN)

        d = {
            "name": k,
            "value": "value for %s" % k,
            "scope": FULL_SYSTEM_SCOPE,
        }
        resp = self.app.put_json("/v1/keys/%s?scope=system" % k, d, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.FORBIDDEN)

        resp = self.app.delete("/v1/keys/%s?scope=system" % k, expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

    def test_user_custom_write_permissions_for_system_scope_kvps(self):
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

        # Set context to user
        self.use_user(self.users[user_db.name])

        # User should be able to list the system and user scoped kvps that user has permission to.
        resp = self.app.get("/v1/keys/")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]["name"], "key1")
        self.assertEqual(resp.json[0]["scope"], FULL_SYSTEM_SCOPE)

        # User should have read and write permissions on system kvp key1.
        k, v = kvp_1_db.name, "val1"
        resp = self.app.get("/v1/keys/%s?decrypt=True&scope=system" % k)
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(resp.json["value"], v)

        d = {
            "name": k,
            "value": "value for %s" % k,
            "scope": FULL_SYSTEM_SCOPE,
            "secret": True,
        }
        resp = self.app.put_json("/v1/keys/%s?scope=system" % k, d)
        self.assertEqual(resp.status_int, http_client.OK)

        resp = self.app.get("/v1/keys/%s?decrypt=True&scope=system" % k)
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(resp.json["value"], "value for %s" % k)

        resp = self.app.delete("/v1/keys/%s?scope=system" % k)
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        resp = self.app.get("/v1/keys/%s?scope=system" % k, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.NOT_FOUND)

        # User should not have read and write permissions on system kvp key2.
        k = kvp_2_db.name
        resp = self.app.get("/v1/keys/%s?scope=system" % k, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.FORBIDDEN)

        d = {
            "name": k,
            "value": "value for %s" % k,
            "scope": FULL_SYSTEM_SCOPE,
        }
        resp = self.app.put_json("/v1/keys/%s?scope=system" % k, d, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.FORBIDDEN)

        resp = self.app.delete("/v1/keys/%s?scope=system" % k, expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

    def test_user_custom_set_permissions_for_system_scope_kvps(self):
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

        # Set context to user
        self.use_user(self.users[user_db.name])

        # User should be able to list the system and user scoped kvps that user has permission to.
        resp = self.app.get("/v1/keys/")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]["name"], "key1")
        self.assertEqual(resp.json[0]["scope"], FULL_SYSTEM_SCOPE)

        # User should have read and set but no delete permissions on system kvp key1.
        k, v = kvp_1_db.name, "val1"
        resp = self.app.get("/v1/keys/%s?decrypt=True&scope=system" % k)
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(resp.json["value"], v)

        d = {
            "name": k,
            "value": "value for %s" % k,
            "scope": FULL_SYSTEM_SCOPE,
            "secret": True,
        }
        resp = self.app.put_json("/v1/keys/%s?scope=system" % k, d)
        self.assertEqual(resp.status_int, http_client.OK)

        resp = self.app.get("/v1/keys/%s?decrypt=True&scope=system" % k)
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(resp.json["value"], "value for %s" % k)

        resp = self.app.delete("/v1/keys/%s?scope=system" % k, expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

        # User should not have read and write permissions on system kvp key2.
        k = kvp_2_db.name
        resp = self.app.get("/v1/keys/%s?scope=system" % k, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.FORBIDDEN)

        d = {
            "name": k,
            "value": "value for %s" % k,
            "scope": FULL_SYSTEM_SCOPE,
        }
        resp = self.app.put_json("/v1/keys/%s?scope=system" % k, d, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.FORBIDDEN)

        resp = self.app.delete("/v1/keys/%s?scope=system" % k, expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

    def test_user_custom_delete_permissions_for_system_scope_kvps(self):
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

        # Set context to user
        self.use_user(self.users[user_db.name])

        # User should be able to list the system and user scoped kvps that user has permission to.
        resp = self.app.get("/v1/keys/")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]["name"], "key1")
        self.assertEqual(resp.json[0]["scope"], FULL_SYSTEM_SCOPE)

        # User should have read and delete but no set permissions on system kvp key1.
        k, v = kvp_1_db.name, "val1"
        resp = self.app.get("/v1/keys/%s?decrypt=True&scope=system" % k)
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(resp.json["value"], v)

        d = {
            "name": k,
            "value": "value for %s" % k,
            "scope": FULL_SYSTEM_SCOPE,
        }
        resp = self.app.put_json("/v1/keys/%s?scope=system" % k, d, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.FORBIDDEN)

        resp = self.app.delete("/v1/keys/%s?scope=system" % k)
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        resp = self.app.get("/v1/keys/%s?scope=system" % k, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.NOT_FOUND)

        # User should not have read and write permissions on system kvp key2.
        k = kvp_2_db.name
        resp = self.app.get("/v1/keys/%s?scope=system" % k, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.FORBIDDEN)

        d = {
            "name": k,
            "value": "value for %s" % k,
            "scope": FULL_SYSTEM_SCOPE,
        }
        resp = self.app.put_json("/v1/keys/%s?scope=system" % k, d, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.FORBIDDEN)

        resp = self.app.delete("/v1/keys/%s?scope=system" % k, expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

    def test_user_custom_all_permissions_for_system_scope_kvps(self):
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

        # Set context to user
        self.use_user(self.users[user_db.name])

        # User should be able to list the system and user scoped kvps that user has permission to.
        resp = self.app.get("/v1/keys/")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]["name"], "key1")
        self.assertEqual(resp.json[0]["scope"], FULL_SYSTEM_SCOPE)

        # User should have read and write permissions on system kvp key1.
        k, v = kvp_1_db.name, "val1"
        resp = self.app.get("/v1/keys/%s?decrypt=True&scope=system" % k)
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(resp.json["value"], v)

        d = {
            "name": k,
            "value": "value for %s" % k,
            "scope": FULL_SYSTEM_SCOPE,
            "secret": True,
        }
        resp = self.app.put_json("/v1/keys/%s?scope=system" % k, d)
        self.assertEqual(resp.status_int, http_client.OK)

        resp = self.app.get("/v1/keys/%s?decrypt=True&scope=system" % k)
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(resp.json["value"], "value for %s" % k)

        resp = self.app.delete("/v1/keys/%s?scope=system" % k)
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        resp = self.app.get("/v1/keys/%s?scope=system" % k, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.NOT_FOUND)

        # User should not have read and write permissions on system kvp key2.
        k = kvp_2_db.name
        resp = self.app.get("/v1/keys/%s?scope=system" % k, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.FORBIDDEN)

        d = {
            "name": k,
            "value": "value for %s" % k,
            "scope": FULL_SYSTEM_SCOPE,
        }
        resp = self.app.put_json("/v1/keys/%s?scope=system" % k, d, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.FORBIDDEN)

        resp = self.app.delete("/v1/keys/%s?scope=system" % k, expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)


class KeyValueUserScopeControllerRBACTestCase(KeyValuesControllerRBACTestCase):
    def setUp(self):
        super(KeyValueUserScopeControllerRBACTestCase, self).setUp()

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

    def test_user_permissions_for_user_scope_kvps(self):
        # Insert user scoped key value pairs for user1.
        user_1_db = UserDB(name="user111")
        user_1_db = User.add_or_update(user_1_db)
        self.users[user_1_db.name] = user_1_db

        key_1_name = "mykey1"
        key_1_ref = get_key_reference(FULL_USER_SCOPE, key_1_name, user_1_db.name)
        kvp_1_api = KeyValuePairSetAPI(
            uid="%s:%s:%s" % (ResourceType.KEY_VALUE_PAIR, FULL_USER_SCOPE, key_1_ref),
            scope=FULL_USER_SCOPE,
            name=key_1_ref,
            value="myval1",
            secret=True,
        )
        kvp_1_db = KeyValuePairSetAPI.to_model(kvp_1_api)
        kvp_1_db = KeyValuePair.add_or_update(kvp_1_db)
        self.resources[kvp_1_db.uid] = kvp_1_db

        # Insert user scoped key value pairs for user2.
        user_2_db = UserDB(name="user112")
        user_2_db = User.add_or_update(user_2_db)
        self.users[user_2_db.name] = user_2_db

        key_2_name = "mykey2"
        key_2_ref = get_key_reference(FULL_USER_SCOPE, key_2_name, user_2_db.name)
        kvp_2_api = KeyValuePairSetAPI(
            uid="%s:%s:%s" % (ResourceType.KEY_VALUE_PAIR, FULL_USER_SCOPE, key_2_ref),
            scope=FULL_USER_SCOPE,
            name=key_2_ref,
            value="myval2",
            secret=True,
        )
        kvp_2_db = KeyValuePairSetAPI.to_model(kvp_2_api)
        kvp_2_db = KeyValuePair.add_or_update(kvp_2_db)
        self.resources[kvp_2_db.uid] = kvp_2_db

        # Set context to user
        self.use_user(self.users[user_1_db.name])

        # User should be able to list the system and user scoped kvps that user has permission to.
        resp = self.app.get("/v1/keys?limit=-1")  # server defaults no scope to system scope
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 0)

        resp = self.app.get("/v1/keys/")  # server defaults no scope to system scope
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 0)

        resp = self.app.get("/v1/keys?scope=all")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 1)
        self.assertTrue(all([item["scope"] == FULL_USER_SCOPE for item in resp.json]))

        resp = self.app.get("/v1/keys?scope=system")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 0)

        resp = self.app.get("/v1/keys?scope=user")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 1)
        self.assertTrue(all([item["scope"] == FULL_USER_SCOPE for item in resp.json]))

        # User should have read and write permissions to his/her own kvps.
        k, v = key_1_name, kvp_1_api.value
        resp = self.app.get("/v1/keys/%s?decrypt=True&scope=user" % k)
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(resp.json["value"], v)

        d = {
            "name": key_1_ref,
            "value": "value for %s" % k,
            "scope": FULL_USER_SCOPE,
            "secret": True,
        }
        resp = self.app.put_json("/v1/keys/%s?scope=user" % k, d)
        self.assertEqual(resp.status_int, http_client.OK)

        resp = self.app.get("/v1/keys/%s?decrypt=True&scope=user" % k)
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(resp.json["value"], "value for %s" % k)

        resp = self.app.delete("/v1/keys/%s?scope=user" % k)
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        resp = self.app.get("/v1/keys/%s?scope=user" % k, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.NOT_FOUND)

    def test_user_permissions_for_another_user_kvps(self):
        # Setup users.
        user_1_db = UserDB(name="user113")
        user_1_db = User.add_or_update(user_1_db)
        self.users[user_1_db.name] = user_1_db

        user_2_db = UserDB(name="user114")
        user_2_db = User.add_or_update(user_2_db)
        self.users[user_2_db.name] = user_2_db

        # Insert user scoped key value pairs for user1.
        key_1_name = "mykey3"
        key_1_ref = get_key_reference(FULL_USER_SCOPE, key_1_name, user_1_db.name)
        kvp_1_api = KeyValuePairSetAPI(
            uid="%s:%s:%s" % (ResourceType.KEY_VALUE_PAIR, FULL_USER_SCOPE, key_1_ref),
            scope=FULL_USER_SCOPE,
            name=key_1_ref,
            value="myval3",
            secret=True,
        )
        kvp_1_db = KeyValuePairSetAPI.to_model(kvp_1_api)
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

        # Set context to user
        self.use_user(self.users[user_2_db.name])

        # User2 should not be able to list user1's kvp.
        resp = self.app.get("/v1/keys?limit=-1")  # server defaults no scope to system scope
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 0)

        resp = self.app.get("/v1/keys/")  # server defaults no scope to system scope
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 0)

        resp = self.app.get("/v1/keys?scope=all")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 0)

        resp = self.app.get("/v1/keys?scope=system")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 0)

        resp = self.app.get("/v1/keys?scope=user")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 0)

        # User2 should not have read and write permissions on user1's kvp.
        k = key_1_name
        url = "/v1/keys/%s?scope=user&user=%s" % (k, user_1_db.name)
        resp = self.app.get(url, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.FORBIDDEN)

        d = {
            "name": key_1_ref,
            "value": "value for %s" % k,
            "scope": FULL_USER_SCOPE,
            "user": user_1_db.name,
        }
        resp = self.app.put_json(url, d, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.FORBIDDEN)

        resp = self.app.delete(url, expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

    def test_admin_permissions_for_user_scoped_kvps(self):
        # Insert user scoped key value pairs for user1.
        user_1_db = UserDB(name="user115")
        user_1_db = User.add_or_update(user_1_db)
        self.users[user_1_db.name] = user_1_db

        key_1_name = "mykey5"
        key_1_ref = get_key_reference(FULL_USER_SCOPE, key_1_name, user_1_db.name)
        kvp_1_api = KeyValuePairSetAPI(
            uid="%s:%s:%s" % (ResourceType.KEY_VALUE_PAIR, FULL_USER_SCOPE, key_1_ref),
            scope=FULL_USER_SCOPE,
            name=key_1_ref,
            value="myval5",
            secret=True,
        )
        kvp_1_db = KeyValuePairSetAPI.to_model(kvp_1_api)
        kvp_1_db = KeyValuePair.add_or_update(kvp_1_db)
        self.resources[kvp_1_db.uid] = kvp_1_db

        # Set context to user
        self.use_user(self.users["admin"])

        # Admin user should have general list permissions on user1's kvps.
        resp = self.app.get("/v1/keys?limit=-1&scope=user&user=%s" % user_1_db.name)
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 1)

        resp = self.app.get("/v1/keys?scope=user&user=%s" % user_1_db.name)
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]["name"], key_1_name)
        self.assertEqual(resp.json[0]["user"], user_1_db.name)

        resp = self.app.get("/v1/keys?decrypt=True&scope=user&user=%s" % user_1_db.name)
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]["name"], key_1_name)
        self.assertEqual(resp.json[0]["user"], user_1_db.name)
        self.assertEqual(resp.json[0]["value"], kvp_1_api.value)

        resp = self.app.get("/v1/keys?scope=all")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 2)
        self.assertTrue(all([item["scope"] == FULL_SYSTEM_SCOPE for item in resp.json]))

        resp = self.app.get("/v1/keys?scope=system")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 2)
        self.assertTrue(all([item["scope"] == FULL_SYSTEM_SCOPE for item in resp.json]))

        resp = self.app.get("/v1/keys?scope=user")
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(len(resp.json), 0)

        # Admin user should have read and write permissions to user1's kvps.
        k, v = key_1_name, kvp_1_api.value
        url = "/v1/keys/%s?decrypt=True&scope=user&user=%s" % (k, user_1_db.name)
        resp = self.app.get(url)
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(resp.json["value"], v)

        d = {
            "name": key_1_ref,
            "value": "value for %s" % k,
            "scope": FULL_USER_SCOPE,
            "user": user_1_db.name,
            "secret": True,
        }
        resp = self.app.put_json(url, d)
        self.assertEqual(resp.status_int, http_client.OK)

        resp = self.app.get(url)
        self.assertEqual(resp.status_int, http_client.OK)
        self.assertEqual(resp.json["value"], "value for %s" % k)

        resp = self.app.delete(url)
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        resp = self.app.get(url, expect_errors=True)
        self.assertEqual(resp.status_int, http_client.NOT_FOUND)
