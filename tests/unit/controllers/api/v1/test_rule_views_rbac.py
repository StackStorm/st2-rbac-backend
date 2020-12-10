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

from st2api.controllers.v1.rule_views import RuleViewController

from tests.unit.controllers.api.v1.test_rules_rbac import BaseRuleControllerRBACTestCase
from st2tests.api import APIControllerWithIncludeAndExcludeFilterTestCase

__all__ = [
    'RuleViewsControllerRBACTestCase'
]


class RuleViewsControllerRBACTestCase(BaseRuleControllerRBACTestCase,
                                      APIControllerWithIncludeAndExcludeFilterTestCase):
    get_all_path = '/v1/rules/views'
    controller_cls = RuleViewController
    include_attribute_field_name = 'criteria'
    exclude_attribute_field_name = 'enabled'
    rbac_enabled = True

    api_endpoint = '/v1/rules/views'

    def _insert_mock_models(self):
        rule_1_id = self._do_post(self.RULE_1).json['id']
        rule_2_id = self._do_post(self.RULE_2).json['id']
        return [rule_1_id, rule_2_id]
