# Copyright (C) 2019 Extreme Networks, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential.
# See the LICENSE file included with this work for details.

from tests.unit.controllers.api.v1.test_rules_rbac import BaseRuleControllerRBACTestCase

__all__ = [
    'RuleViewsControllerRBACTestCase'
]


class RuleViewsControllerRBACTestCase(BaseRuleControllerRBACTestCase):
    api_endpoint = '/v1/rules/views'
