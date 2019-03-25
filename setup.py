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

import os

from setuptools import setup, find_packages

from dist_utils import check_pip_version
from dist_utils import fetch_requirements
from dist_utils import parse_version_string

check_pip_version()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS_FILE = os.path.join(BASE_DIR, 'requirements.txt')
INIT_FILE = os.path.join(BASE_DIR, 'st2rbac_enterprise_backend_default', '__init__.py')

version = parse_version_string(INIT_FILE)
install_reqs, dep_links = fetch_requirements(REQUIREMENTS_FILE)

setup(
    name='st2-enterprise-rbac-backend-default',
    version=version,
    description='Enterprise RBAC backend for StackStorm.',
    author='StackStorm, Inc.',
    author_email='info@stackstorm.com',
    url='https://github.com/StackStorm/st2-enterprise-rbac-backend-default',
    license='Proprietary License',
    download_url=(
        'https://github.com/StackStorm/st2-enterprise-rbac-backend-default/tarball/master'
    ),
    classifiers=[
        'License :: Other/Proprietary License'
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Environment :: Console',
    ],
    platforms=['Any'],
    scripts=[],
    provides=['st2rbac_enterprise_backend_default'],
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_reqs,
    dependency_links=dep_links,
    test_suite='tests',
    entry_points={
        'st2rbac.backends.backend': [
            'enterprise = st2rbac_enterprise_backend_default.',
        ],
    },
    zip_safe=False
)
