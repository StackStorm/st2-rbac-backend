# Copyright (c) Extreme Networks, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""
A script which applies RBAC definitions and role assignments stored on disk.
"""

from __future__ import absolute_import

from st2common import config
from st2common.script_setup import setup as common_setup
from st2common.script_setup import teardown as common_teardown

from st2rbac_enterprise_backend.loader import RBACDefinitionsLoader
from st2rbac_enterprise_backend.syncer import RBACDefinitionsDBSyncer

__all__ = [
    'main'
]


def setup(argv):
    common_setup(config=config, setup_db=True, register_mq_exchanges=True)


def teartown():
    common_teardown()


def apply_definitions():
    loader = RBACDefinitionsLoader()
    result = loader.load()

    role_definition_apis = list(result['roles'].values())
    role_assignment_apis = list(result['role_assignments'].values())
    group_to_role_map_apis = list(result['group_to_role_maps'].values())

    syncer = RBACDefinitionsDBSyncer()
    result = syncer.sync(role_definition_apis=role_definition_apis,
                         role_assignment_apis=role_assignment_apis,
                         group_to_role_map_apis=group_to_role_map_apis)

    return result


def main(argv):
    setup(argv)
    apply_definitions()
    teartown()
