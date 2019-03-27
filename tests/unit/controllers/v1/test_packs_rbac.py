# Copyright (c) Extreme Networks, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

import mock
import six

from st2common.router import Response
from st2common.services import packs as pack_service
from st2api.controllers.v1.actionexecutions import ActionExecutionsControllerMixin

from tests.base import APIControllerWithRBACTestCase

http_client = six.moves.http_client

__all__ = [
    'PackControllerRBACTestCase'
]

PACK_INDEX = {
    "test": {
        "version": "0.4.0",
        "name": "test",
        "repo_url": "https://github.com/StackStorm-Exchange/stackstorm-test",
        "author": "st2-dev",
        "keywords": ["some", "search", "another", "terms"],
        "email": "info@stackstorm.com",
        "description": "st2 pack to test package management pipeline"
    },
    "test2": {
        "version": "0.5.0",
        "name": "test2",
        "repo_url": "https://github.com/StackStorm-Exchange/stackstorm-test2",
        "author": "stanley",
        "keywords": ["some", "special", "terms"],
        "email": "info@stackstorm.com",
        "description": "another st2 pack to test package management pipeline"
    }
}


class PackControllerRBACTestCase(APIControllerWithRBACTestCase):
    @mock.patch.object(ActionExecutionsControllerMixin, '_handle_schedule_execution')
    def test_install(self, _handle_schedule_execution):
        user_db = self.users['system_admin']
        self.use_user(user_db)

        _handle_schedule_execution.return_value = Response(json={'id': '123'})
        payload = {'packs': ['some']}

        resp = self.app.post_json('/v1/packs/install', payload)

        self.assertEqual(resp.status_int, 202)
        self.assertEqual(resp.json, {'execution_id': '123'})

        # Verify created execution correctly used the user which performed the API operation
        call_kwargs = _handle_schedule_execution.call_args[1]
        self.assertEqual(call_kwargs['requester_user'], user_db)
        self.assertEqual(call_kwargs['liveaction_api'].user, user_db.name)

        # Try with a different user
        user_db = self.users['admin']
        self.use_user(user_db)

        resp = self.app.post_json('/v1/packs/install', payload)

        self.assertEqual(resp.status_int, 202)
        self.assertEqual(resp.json, {'execution_id': '123'})

        # Verify created execution correctly used the user which performed the API operation
        call_kwargs = _handle_schedule_execution.call_args[1]
        self.assertEqual(call_kwargs['requester_user'], user_db)
        self.assertEqual(call_kwargs['liveaction_api'].user, user_db.name)

    @mock.patch.object(ActionExecutionsControllerMixin, '_handle_schedule_execution')
    def test_uninstall(self, _handle_schedule_execution):
        user_db = self.users['system_admin']
        self.use_user(user_db)

        _handle_schedule_execution.return_value = Response(json={'id': '123'})
        payload = {'packs': ['some']}

        resp = self.app.post_json('/v1/packs/uninstall', payload)

        self.assertEqual(resp.status_int, 202)
        self.assertEqual(resp.json, {'execution_id': '123'})

        # Verify created execution correctly used the user which performed the API operation
        call_kwargs = _handle_schedule_execution.call_args[1]
        self.assertEqual(call_kwargs['requester_user'], user_db)
        self.assertEqual(call_kwargs['liveaction_api'].user, user_db.name)

    def test_get_all_limit_minus_one(self):
        user_db = self.users['observer']
        self.use_user(user_db)

        resp = self.app.get('/v1/packs?limit=-1', expect_errors=True)
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)

        user_db = self.users['admin']
        self.use_user(user_db)

        resp = self.app.get('/v1/packs?limit=-1')
        self.assertEqual(resp.status_code, http_client.OK)

    @mock.patch.object(pack_service, 'fetch_pack_index',
                       mock.MagicMock(return_value=(PACK_INDEX, {})))
    def test_pack_search(self):
        user_db = self.users['no_permissions']
        self.use_user(user_db)

        data = {'query': 'test'}
        resp = self.app.post_json('/v1/packs/index/search', data, expect_errors=True)

        expected_msg = 'User \"no_permissions\" doesn\'t have required permission \"pack_search\"'
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)
        self.assertEqual(resp.json['faultstring'], expected_msg)

        # Observer role also grants pack_search permission
        user_db = self.users['observer']
        self.use_user(user_db)

        data = {'query': 'test'}
        resp = self.app.post_json('/v1/packs/index/search', data)
        self.assertEqual(resp.status_code, http_client.OK)
