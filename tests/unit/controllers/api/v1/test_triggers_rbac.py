# Copyright 2026 The StackStorm Authors.
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

import mock
import six

from st2common.rbac.types import PermissionType
from st2common.rbac.types import ResourceType
from st2common.persistence.auth import User
from st2common.persistence.rbac import Role
from st2common.persistence.rbac import UserRoleAssignment
from st2common.persistence.rbac import PermissionGrant
from st2common.models.db.auth import UserDB
from st2common.models.db.rbac import RoleDB
from st2common.models.db.rbac import UserRoleAssignmentDB
from st2common.models.db.rbac import PermissionGrantDB
from st2common.transport.reactor import TriggerDispatcher
from st2tests.fixturesloader import FixturesLoader

from tests.base import APIControllerWithRBACTestCase

http_client = six.moves.http_client

__all__ = ["TriggerControllersRBACTestCase"]

FIXTURES_PACK = "generic"
TEST_FIXTURES = {
    "triggertypes": ["triggertype1.yaml"],
    "triggers": ["trigger1.yaml"],
    "triggerinstances": ["trigger_instance_1.yaml"],
}

MOCK_TRIGGER_TYPE_1 = {
    "name": "triggertype-3",
    "pack": "wolfpack",
    "parameters_schema": {},
    "payload_schema": {},
}

ADMIN_REQUIRED_MSG = "Administrator access required"


class TriggerControllersRBACTestCase(APIControllerWithRBACTestCase):
    fixtures_loader = FixturesLoader()

    def setUp(self):
        super(TriggerControllersRBACTestCase, self).setUp()
        self.models = self.fixtures_loader.save_fixtures_to_db(
            fixtures_pack=FIXTURES_PACK, fixtures_dict=TEST_FIXTURES
        )
        self.trigger_type_db = self.models["triggertypes"]["triggertype1.yaml"]
        self.trigger_db = self.models["triggers"]["trigger1.yaml"]
        self.trigger_instance_db = self.models["triggerinstances"]["trigger_instance_1.yaml"]

        # trigger_list
        grant_db = PermissionGrantDB(
            resource_uid=None,
            resource_type=ResourceType.TRIGGER,
            permission_types=[PermissionType.TRIGGER_LIST],
        )
        self._add_user_with_grant("trigger_list", grant_db)

        # trigger_view on trigger 1
        grant_db = PermissionGrantDB(
            resource_uid=self.trigger_db.get_uid(),
            resource_type=ResourceType.TRIGGER,
            permission_types=[PermissionType.TRIGGER_VIEW],
        )
        self._add_user_with_grant("trigger_view", grant_db)

    def _add_user_with_grant(self, name, grant_db):
        user_db = User.add_or_update(UserDB(name=name))
        self.users[name] = user_db

        grant_db = PermissionGrant.add_or_update(grant_db)
        role_db = Role.add_or_update(RoleDB(name=name, permission_grants=[str(grant_db.id)]))
        self.roles[name] = role_db

        UserRoleAssignment.add_or_update(
            UserRoleAssignmentDB(
                user=user_db.name, role=role_db.name, source="assignments/%s.yaml" % name
            )
        )

    def _assert_forbidden(self, resp, expected_msg):
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)
        self.assertIn(expected_msg, resp.json["faultstring"])

    def test_trigger_list_can_list_and_view_trigger_types(self):
        self.use_user(self.users["trigger_list"])

        resp = self.app.get("/v1/triggertypes")
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertIn(self.trigger_type_db.ref, [item["ref"] for item in resp.json])

        resp = self.app.get("/v1/triggertypes/%s" % (self.trigger_type_db.ref))
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(resp.json["ref"], self.trigger_type_db.ref)

    def test_trigger_list_can_list_triggers_but_not_view_one(self):
        self.use_user(self.users["trigger_list"])

        resp = self.app.get("/v1/triggers")
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertIn(self.trigger_db.get_uid(), [item["uid"] for item in resp.json])

        resp = self.app.get("/v1/triggers/%s" % (self.trigger_db.id), expect_errors=True)
        self._assert_forbidden(
            resp,
            'User "trigger_list" doesn\'t have required permission "trigger_view"'
            ' on resource "%s"' % (self.trigger_db.get_uid()),
        )

    def test_trigger_view_can_view_trigger_but_not_list(self):
        self.use_user(self.users["trigger_view"])

        resp = self.app.get("/v1/triggers/%s" % (self.trigger_db.id))
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(resp.json["uid"], self.trigger_db.get_uid())

        resp = self.app.get("/v1/triggers", expect_errors=True)
        self._assert_forbidden(
            resp, 'User "trigger_view" doesn\'t have required permission "trigger_list"'
        )

        resp = self.app.get("/v1/triggertypes/%s" % (self.trigger_type_db.ref), expect_errors=True)
        self._assert_forbidden(
            resp, 'User "trigger_view" doesn\'t have required permission "trigger_list"'
        )

    def test_trigger_list_cannot_modify_trigger_types_or_triggers(self):
        self.use_user(self.users["trigger_list"])

        resp = self.app.post_json("/v1/triggertypes", MOCK_TRIGGER_TYPE_1, expect_errors=True)
        self._assert_forbidden(resp, ADMIN_REQUIRED_MSG)

        resp = self.app.delete(
            "/v1/triggertypes/%s" % (self.trigger_type_db.ref), expect_errors=True
        )
        self._assert_forbidden(resp, ADMIN_REQUIRED_MSG)

        resp = self.app.delete("/v1/triggers/%s" % (self.trigger_db.id), expect_errors=True)
        self._assert_forbidden(resp, ADMIN_REQUIRED_MSG)

    def test_observer_cannot_read_trigger_instances(self):
        # Observer holds every view and list permission, so this is the widest
        # non-admin grant there is.
        self.use_user(self.users["observer"])

        resp = self.app.get("/v1/triggerinstances", expect_errors=True)
        self._assert_forbidden(resp, ADMIN_REQUIRED_MSG)

        resp = self.app.get(
            "/v1/triggerinstances/%s" % (self.trigger_instance_db.id), expect_errors=True
        )
        self._assert_forbidden(resp, ADMIN_REQUIRED_MSG)

    @mock.patch.object(TriggerDispatcher, "dispatch", mock.MagicMock())
    def test_observer_cannot_re_emit_trigger_instance(self):
        self.use_user(self.users["observer"])

        resp = self.app.post_json(
            "/v1/triggerinstances/%s/re_emit" % (self.trigger_instance_db.id),
            {},
            expect_errors=True,
        )
        self._assert_forbidden(resp, ADMIN_REQUIRED_MSG)
        TriggerDispatcher.dispatch.assert_not_called()

    @mock.patch.object(TriggerDispatcher, "dispatch", mock.MagicMock())
    def test_admin_can_read_and_re_emit_trigger_instances(self):
        self.use_user(self.users["admin"])

        resp = self.app.get("/v1/triggerinstances")
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertIn(str(self.trigger_instance_db.id), [item["id"] for item in resp.json])

        resp = self.app.get("/v1/triggerinstances/%s" % (self.trigger_instance_db.id))
        self.assertEqual(resp.status_code, http_client.OK)

        resp = self.app.post_json(
            "/v1/triggerinstances/%s/re_emit" % (self.trigger_instance_db.id), {}
        )
        self.assertEqual(resp.status_code, http_client.OK)
        TriggerDispatcher.dispatch.assert_called_once()
