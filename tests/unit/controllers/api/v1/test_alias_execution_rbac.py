# Copyright (C) 2019 Extreme Networks, Inc - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly
# prohibited. Proprietary and confidential. See the LICENSE file
# included with this work for details.

import mock

from st2common.constants.action import LIVEACTION_STATUS_SUCCEEDED
from st2common.models.db.execution import ActionExecutionDB
from st2common.services import action as action_service
from st2tests.fixturesloader import FixturesLoader

from tests.base import APIControllerWithRBACTestCase

FIXTURES_PACK = 'aliases'

TEST_MODELS = {
    'aliases': ['alias1.yaml', 'alias2.yaml'],
    'actions': ['action1.yaml'],
    'runners': ['runner1.yaml']
}

TEST_LOAD_MODELS = {
    'aliases': ['alias3.yaml']
}

EXECUTION = ActionExecutionDB(id='54e657d60640fd16887d6855',
                              status=LIVEACTION_STATUS_SUCCEEDED,
                              result='')

__all__ = [
    'AliasExecutionWithRBACTestCase'
]


class AliasExecutionWithRBACTestCase(APIControllerWithRBACTestCase):

    def setUp(self):
        super(AliasExecutionWithRBACTestCase, self).setUp()

        self.models = FixturesLoader().save_fixtures_to_db(fixtures_pack=FIXTURES_PACK,
                                                           fixtures_dict=TEST_MODELS)
        self.alias1 = self.models['aliases']['alias1.yaml']
        self.alias2 = self.models['aliases']['alias2.yaml']

    @mock.patch.object(action_service, 'request',
                       return_value=(None, EXECUTION))
    def test_live_action_context_user_is_set_to_authenticated_user(self, request):
        # Verify that the user inside the context of live action is set to authenticated user
        # which hit the endpoint. This is important for RBAC and many other things.
        user_db = self.users['admin']
        self.use_user(user_db)

        command = 'Lorem ipsum value1 dolor sit "value2, value3" amet.'
        post_resp = self._do_post(alias_execution=self.alias2, command=command)
        self.assertEqual(post_resp.status_int, 201)

        live_action_db = request.call_args[0][0]
        self.assertEquals(live_action_db.context['user'], 'admin')

    def _do_post(self, alias_execution, command, expect_errors=False):
        if (isinstance(alias_execution.formats[0], dict) and
           alias_execution.formats[0].get('representation')):
            representation = alias_execution.formats[0].get('representation')[0]
        else:
            representation = alias_execution.formats[0]
        execution = {'name': alias_execution.name,
                     'format': representation,
                     'command': command,
                     'user': 'stanley',
                     'source_channel': 'test',
                     'notification_route': 'test'}
        return self.app.post_json('/v1/aliasexecution', execution,
                                  expect_errors=expect_errors)
