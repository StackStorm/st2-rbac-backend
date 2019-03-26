# Licensed to the StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from st2common.rbac.backends.base import BaseRBACBackend

from st2rbac_enterprise_backend import resolvers
from st2rbac_enterprise_backend.syncer import RBACRemoteGroupToRoleSyncer

__all__ = [
    'EnterpriseRBACBackend'
]


class EnterpriseRBACBackend(BaseRBACBackend):
    def get_resolver_for_resource_type(self, resource_type):
        return resolvers.get_resolver_for_resource_type(resource_type=resource_type)

    def get_resolver_for_permission_type(self, permission_type):
        return resolvers.get_resolver_for_permission_type(permission_type=permission_type)

    def get_remote_group_to_role_syncer(self):
        return RBACRemoteGroupToRoleSyncer()
