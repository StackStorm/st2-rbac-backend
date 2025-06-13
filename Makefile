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

ROOT_DIR ?= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
CURRENT_DIR ?= $(shell pwd)
VIRTUALENV_DIR ?= virtualenv
ST2_REPO_PATH ?= /tmp/st2
ST2_REPO_URL ?= https://github.com/StackStorm/st2.git
ST2_REPO_BRANCH ?= master

# nasty hack to get a space into a variable
empty:=
space_char:= $(empty) $(empty)
colon := :
comma := ,
dot := .
slash := /

# All components are prefixed by st2
COMPONENTS = $(wildcard $(ST2_REPO_PATH)/st2*)
COMPONENTS_RUNNERS := $(wildcard $(ST2_REPO_PATH)/contrib/runners/*)
COMPONENTS_WITH_RUNNERS := $(COMPONENTS) $(COMPONENTS_RUNNERS)
COMPONENT_PYTHONPATH = $(subst $(space_char),:,$(realpath $(COMPONENTS_WITH_RUNNERS))):$(ST2_REPO_PATH):$(CURRENT_DIR)
COMPONENTS_TEST := $(foreach component,$(filter-out $(COMPONENT_SPECIFIC_TESTS),$(COMPONENTS_WITH_RUNNERS)),$(component))
COMPONENTS_TEST_COMMA := $(subst $(slash),$(dot),$(subst $(space_char),$(comma),$(COMPONENTS_TEST)))
COMPONENTS_TEST_MODULES := $(subst $(slash),$(dot),$(COMPONENTS_TEST_DIRS))
COMPONENTS_TEST_MODULES_COMMA := $(subst $(space_char),$(comma),$(COMPONENTS_TEST_MODULES))

ifndef PYLINT_CONCURRENCY
	PYLINT_CONCURRENCY := 1
endif

NOSE_OPTS := --rednose --immediate --with-parallel

ifndef NOSE_TIME
	NOSE_TIME := yes
endif

ifeq ($(NOSE_TIME),yes)
	NOSE_OPTS := --rednose --immediate --with-parallel --with-timer
	NOSE_WITH_TIMER := 1
endif

ifndef PIP_OPTIONS
	PIP_OPTIONS :=
endif

# Target for debugging Makefile variable assembly
.PHONY: play
play:
	@echo COMPONENTS=$(COMPONENTS)
	@echo COMPONENTS_RUNNERS=$(COMPONENTS_RUNNERS)
	@echo COMPONENTS_WITH_RUNNERS=$(COMPONENTS_WITH_RUNNERS)
	@echo COMPONENT_PYTHONPATH=$(COMPONENT_PYTHONPATH)
	@echo TRAVIS_PULL_REQUEST=$(TRAVIS_PULL_REQUEST)
	@echo NOSE_OPTS=$(NOSE_OPTS)
	@echo
	@echo "`cat /etc/os-release`"
	@echo

.PHONY: all
all: requirements lint

.PHONY: all-ci
all-ci: compile .flake8 .pylint

.PHONY: lint
lint: requirements flake8 pylint black-check

.PHONY: .lint
.lint: compile .flake8 .pylint .black-check

.PHONY: black-check
black-check: requirements .clone_st2_repo .black-check

.PHONY: flake8
flake8: requirements .clone_st2_repo .flake8

.PHONY: pylint
pylint: requirements .clone_st2_repo .pylint

.PHONY: compile
compile:
	@echo "======================= compile ========================"
	@echo "------- Compile all .py files (syntax check test - Python 2) ------"
	@if python -c 'import compileall,re; compileall.compile_dir(".", rx=re.compile(r"/virtualenv|virtualenv-osx|virtualenv-py3|.tox|.git|.venv-st2devbox"), quiet=True)' | grep .; then exit 1; else exit 0; fi

.PHONY: compilepy3
compilepy3:
	@echo "======================= compile ========================"
	@echo "------- Compile all .py files (syntax check test - Python 3) ------"
	@if python3 -c 'import compileall,re; compileall.compile_dir(".", rx=re.compile(r"/virtualenv|virtualenv-osx|virtualenv-py3|.tox|.git|.venv-st2devbox|./st2tests/st2tests/fixtures/packs/test"), quiet=True)' | grep .; then exit 1; else exit 0; fi

.PHONY: .flake8
.flake8:
	@echo
	@echo "==================== flake8 ===================="
	@echo
	. $(VIRTUALENV_DIR)/bin/activate; flake8 --config=lint-configs/python/.flake8 st2rbac_backend/ tests/

.PHONY: .pylint
.pylint:
	@echo
	@echo "==================== pylint ===================="
	@echo
	. $(VIRTUALENV_DIR)/bin/activate; pylint -j $(PYLINT_CONCURRENCY) -E --rcfile=./lint-configs/python/.pylintrc --load-plugins=pylint_plugins.api_models --load-plugins=pylint_plugins.db_models st2rbac_backend/

.PHONY: .black-check
.black-check:
	@echo
	@echo "================== black ===================="
	@echo
	. $(VIRTUALENV_DIR)/bin/activate; black st2rbac_backend bin setup.py -l 100 --check

.PHONY: .black-format
.black-format:
	@echo
	@echo "================== black ===================="
	@echo
	. $(VIRTUALENV_DIR)/bin/activate; black st2rbac_backend bin setup.py -l 100

.PHONY: .unit-tests
.unit-tests:
	@echo
	@echo "==================== unit-tests ===================="
	@echo
	. $(VIRTUALENV_DIR)/bin/activate; nosetests $(NOSE_OPTS) -s -v tests/unit/
	. $(VIRTUALENV_DIR)/bin/activate; nosetests $(NOSE_OPTS) -s -v tests/unit/controllers/api/v1/
	. $(VIRTUALENV_DIR)/bin/activate; nosetests $(NOSE_OPTS) -s -v tests/unit/controllers/stream/v1/

.PHONY: .integration-tests
.integration-tests:
	@echo
	@echo "==================== integration-tests ===================="
	@echo
	. $(VIRTUALENV_DIR)/bin/activate; nosetests $(NOSE_OPTS) -s -v tests/integration/

.PHONY: .unit-tests-py3
.unit-tests-py3:
	@echo
	@echo "==================== unit-tests-py3 ===================="
	@echo
	NOSE_WITH_TIMER=$(NOSE_WITH_TIMER) tox -e py38-unit -vv

.PHONY: .clone_st2_repo
.clone_st2_repo: /tmp/st2
/tmp/st2:
	@echo
	@echo "==================== cloning st2 repo ===================="
	@echo
	@rm -rf /tmp/st2
	@git clone $(ST2_REPO_URL)  --depth 1 --single-branch --branch $(ST2_REPO_BRANCH) $(ST2_REPO_PATH)

# NOTE: We pass --no-deps to the script so we don't install all the
# package dependencies which are already installed as part of "requirements"
# make targets. This speeds up the build
.PHONY: .install-runners-and-deps
.install-runners-and-deps:
	@echo ""
	@echo "================== install runners ===================="
	@echo ""
	@for component in $(COMPONENTS_RUNNERS); do \
		echo "==========================================================="; \
		echo "Installing runner:" $$component; \
		echo "==========================================================="; \
        	(. $(VIRTUALENV_DIR)/bin/activate; cd $$component; python3 setup.py develop --no-deps); \
	done
	@echo ""
	@echo "================== register metrics drivers ======================"
	@echo ""
	# Install st2common to register metrics drivers
	(. $(VIRTUALENV_DIR)/bin/activate; cd $(ST2_REPO_PATH)/st2common; python3 setup.py develop --no-deps)
	@echo ""
	@echo "================== register rbac backend ======================"
	@echo ""
	(. $(VIRTUALENV_DIR)/bin/activate; python3 setup.py develop --no-deps)

# NOTE: We pass --no-deps to the script so we don't install all the
# package dependencies which are already installed as part of "requirements"
# make targets. This speeds up the build
.PHONY: requirements
requirements: .clone_st2_repo virtualenv
	@echo
	@echo "==================== requirements ===================="
	@echo
	#. $(VIRTUALENV_DIR)/bin/activate && $(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache $(PIP_OPTIONS) -r /tmp/st2/requirements.txt
	#. $(VIRTUALENV_DIR)/bin/activate && $(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache $(PIP_OPTIONS) -r /tmp/st2/test-requirements.txt
	$(eval PIP_VERSION := $(shell grep 'PIP_VERSION ?= ' /tmp/st2/Makefile | awk '{ print $$3}'))
	$(VIRTUALENV_DIR)/bin/pip install --upgrade "pip==$(PIP_VERSION)"
	$(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache $(PIP_OPTIONS) -r $(ST2_REPO_PATH)/requirements.txt
	$(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache $(PIP_OPTIONS) -r $(ST2_REPO_PATH)/test-requirements.txt
	$(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache $(PIP_OPTIONS) -r requirements.txt
	$(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache $(PIP_OPTIONS) -r test-requirements.txt
	@echo ""
	@echo "================== install runners ===================="
	@echo ""
	@for component in $(COMPONENTS_RUNNERS); do \
        echo "==========================================================="; \
        echo "Installing runner:" $$component; \
        echo "==========================================================="; \
        (. $(VIRTUALENV_DIR)/bin/activate; cd $$component; python3 setup.py develop); \
	done
	@echo ""
	@echo "================== register metrics drivers ======================"
	@echo ""
	# Install st2common to register metrics drivers
	(. $(VIRTUALENV_DIR)/bin/activate; cd $(ST2_REPO_PATH)/st2common; python3 setup.py develop --no-deps)
	@echo ""
	@echo "================== register rbac backend ======================"
	@echo ""
	(. $(VIRTUALENV_DIR)/bin/activate; python3 setup.py develop --no-deps)

.PHONY: requirements-ci
requirements-ci:
	@echo
	@echo "==================== requirements-ci ===================="
	@echo
	#. $(VIRTUALENV_DIR)/bin/activate && $(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache $(PIP_OPTIONS) -r /tmp/st2/requirements.txt
	#. $(VIRTUALENV_DIR)/bin/activate && $(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache $(PIP_OPTIONS) -r /tmp/st2/test-requirements.txt
	$(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache $(PIP_OPTIONS) -r $(ST2_REPO_PATH)/requirements.txt
	$(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache $(PIP_OPTIONS) -r $(ST2_REPO_PATH)/test-requirements.txt
	$(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache $(PIP_OPTIONS) -r requirements.txt
	$(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache $(PIP_OPTIONS) -r test-requirements.txt

.PHONY: virtualenv
virtualenv: $(VIRTUALENV_DIR)/bin/activate
$(VIRTUALENV_DIR)/bin/activate:
	@echo
	@echo "==================== virtualenv ===================="
	@echo
	test -d $(VIRTUALENV_DIR) || virtualenv $(VIRTUALENV_DIR) -p python3

	# Setup PYTHONPATH in bash activate script...
	# Delete existing entries (if any)
ifeq ($(OS),Darwin)
	echo 'Setting up virtualenv on $(OS)...'
	sed -i '' '/_OLD_PYTHONPATHp/d' $(VIRTUALENV_DIR)/bin/activate
	sed -i '' '/PYTHONPATH=/d' $(VIRTUALENV_DIR)/bin/activate
	sed -i '' '/export PYTHONPATH/d' $(VIRTUALENV_DIR)/bin/activate
else
	echo 'Setting up virtualenv on $(OS)...'
	sed -i '/_OLD_PYTHONPATHp/d' $(VIRTUALENV_DIR)/bin/activate
	sed -i '/PYTHONPATH=/d' $(VIRTUALENV_DIR)/bin/activate
	sed -i '/export PYTHONPATH/d' $(VIRTUALENV_DIR)/bin/activate
endif

	echo '_OLD_PYTHONPATH=$$PYTHONPATH' >> $(VIRTUALENV_DIR)/bin/activate
	echo 'PYTHONPATH=$(COMPONENT_PYTHONPATH)' >> $(VIRTUALENV_DIR)/bin/activate
	echo 'export PYTHONPATH' >> $(VIRTUALENV_DIR)/bin/activate
	touch $(VIRTUALENV_DIR)/bin/activate
