# Copyright (C) 2020 Extreme Networks, Inc - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly
# prohibited. Proprietary and confidential. See the LICENSE file
# included with this work for details.

from tests.base import APIControllerWithRBACTestCase

__all__ = [
    'UserControllerTestCase'
]


class UserControllerTestCase(APIControllerWithRBACTestCase):
    def test_get(self):
        self.use_user(self.users['observer'])
        resp = self.app.get('/v1/user')
        self.assertEqual(resp.json['username'], 'observer')
        self.assertEqual(resp.json['rbac']['enabled'], True)
        self.assertEqual(resp.json['rbac']['is_admin'], False)
        self.assertEqual(resp.json['rbac']['roles'], ['observer'])
        self.assertEqual(resp.json['authentication']['method'], 'authentication token')
        self.assertEqual(resp.json['authentication']['location'], 'header')
        self.use_user(self.users['admin'])

        resp = self.app.get('/v1/user')
        self.assertEqual(resp.json['username'], 'admin')
        self.assertEqual(resp.json['rbac']['enabled'], True)
        self.assertEqual(resp.json['rbac']['is_admin'], True)
        self.assertEqual(resp.json['rbac']['roles'], ['admin'])
        self.assertEqual(resp.json['authentication']['method'], 'authentication token')
        self.assertEqual(resp.json['authentication']['location'], 'header')
