# Copyright (c) Extreme Networks, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential.
# See the LICENSE file included with this work for details.

from st2common.rbac.backends.base import BaseRBACBackend

from st2rbac_enterprise_backend import resolvers
from st2rbac_enterprise_backend.utils import RBACUtils
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

    def get_utils_class(self):
        return RBACUtils
