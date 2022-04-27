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

from st2tests.fixturesloader import FixturesLoader
from st2api.controllers.v1.runnertypes import RunnerTypesController

from tests.base import APIControllerWithRBACTestCase
from st2tests.api import APIControllerWithIncludeAndExcludeFilterTestCase

http_client = six.moves.http_client

__all__ = [
    'RunnerTypesControllerRBACTestCase'
]

FIXTURES_PACK = 'generic'
TEST_FIXTURES = {
    'runners': ['testrunner1.yaml'],
    'actions': ['action1.yaml', 'local.yaml'],
    'triggers': ['trigger1.yaml'],
    'triggertypes': ['triggertype1.yaml']
}


class RunnerTypesControllerRBACTestCase(APIControllerWithRBACTestCase,
                                        APIControllerWithIncludeAndExcludeFilterTestCase):

    # Attributes used by APIControllerWithIncludeAndExcludeFilterTestCase
    get_all_path = '/v1/runnertypes'
    controller_cls = RunnerTypesController
    include_attribute_field_name = 'runner_package'
    exclude_attribute_field_name = 'runner_module'
    test_exact_object_count = False  # runners are registered dynamically in base test class
    rbac_enabled = True

    fixtures_loader = FixturesLoader()

    def setUp(self):
        super(RunnerTypesControllerRBACTestCase, self).setUp()
        self.fixtures_loader.save_fixtures_to_db(fixtures_pack=FIXTURES_PACK,
                                                 fixtures_dict=TEST_FIXTURES)

    def test_get_all_and_get_one_no_permissions(self):
        # get all
        user_db = self.users['no_permissions']
        self.use_user(user_db)

        resp = self.app.get('/v1/runnertypes', expect_errors=True)
        expected_msg = ('User "no_permissions" doesn\'t have required permission '
                        '"runner_type_list"')
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)
        self.assertEqual(resp.json['faultstring'], expected_msg)

        # get one
        resp = self.app.get('/v1/runnertypes/test-runner-1', expect_errors=True)
        expected_msg = ('User "no_permissions" doesn\'t have required permission '
                        '"runner_type_view" on resource "runner_type:test-runner-1"')
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)
        self.assertEqual(resp.json['faultstring'], expected_msg)

    def test_put_disable_runner_no_permissions(self):
        user_db = self.users['admin']
        self.use_user(user_db)

        runnertype_id = 'test-runner-1'
        resp = self.app.get('/v1/runnertypes/%s' % runnertype_id)

        # Disable the runner
        user_db = self.users['no_permissions']
        self.use_user(user_db)

        update_input = resp.json
        update_input['enabled'] = False

        resp = self.__do_put(runnertype_id, update_input)
        expected_msg = ('User "no_permissions" doesn\'t have required permission '
                        '"runner_type_modify" on resource "runner_type:test-runner-1"')
        self.assertEqual(resp.status_code, http_client.FORBIDDEN)
        self.assertEqual(resp.json['faultstring'], expected_msg)

    def __do_put(self, runner_type_id, runner_type):
        return self.app.put_json('/v1/runnertypes/%s' % runner_type_id, runner_type,
                                expect_errors=True)
