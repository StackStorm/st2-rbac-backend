# Copyright (C) 2020 Extreme Networks, Inc - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly
# prohibited. Proprietary and confidential. See the LICENSE file
# included with this work for details.

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
