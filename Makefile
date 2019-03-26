ROOT_DIR ?= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

VIRTUALENV_DIR ?= virtualenv
ST2_REPO_PATH ?= /tmp/st2
ST2_REPO_BRANCH ?= master

export ST2_REPO_PATH

# nasty hack to get a space into a variable
colon := :
comma := ,
dot := .
slash := /
space_char :=
space_char +=

# All components are prefixed by st2
COMPONENTS = $(wildcard $(ST2_REPO_PATH)/st2*)
COMPONENTS_RUNNERS := $(wildcard $(ST2_REPO_PATH)/st2/contrib/runners/*)
COMPONENT_PYTHONPATH = $(subst $(space_char),:,$(realpath $(COMPONENTS)))
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
	@echo
	@echo COMPONENTS_WITH_RUNNERS=$(COMPONENTS_WITH_RUNNERS)
	@echo
	@echo COMPONENTS_TEST=$(COMPONENTS_TEST)
	@echo
	@echo COMPONENTS_TEST_COMMA=$(COMPONENTS_TEST_COMMA)
	@echo
	@echo COMPONENTS_TEST_DIRS=$(COMPONENTS_TEST_DIRS)
	@echo
	@echo COMPONENTS_TEST_MODULES=$(COMPONENTS_TEST_MODULES)
	@echo
	@echo COMPONENTS_TEST_MODULES_COMMA=$(COMPONENTS_TEST_MODULES_COMMA)
	@echo
	@echo COMPONENT_PYTHONPATH=$(COMPONENT_PYTHONPATH)
	@echo
	@echo TRAVIS_PULL_REQUEST=$(TRAVIS_PULL_REQUEST)
	@echo
	@echo NOSE_OPTS=$(NOSE_OPTS)
	@echo

.PHONY: all
all: requirements lint

.PHONY: all-ci
all-ci: compile .flake8 .pylint

.PHONY: lint
lint: requirements flake8 pylint

.PHONY: .lint
.lint: .flake8 .pylint

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
	. $(VIRTUALENV_DIR)/bin/activate; flake8 --config=lint-configs/python/.flake8 st2rbac_enterprise_backend_default/

.PHONY: .pylint
.pylint:
	@echo
	@echo "==================== pylint ===================="
	@echo
	. $(VIRTUALENV_DIR)/bin/activate; pylint -j $(PYLINT_CONCURRENCY) -E --rcfile=./lint-configs/python/.pylintrc --load-plugins=pylint_plugins.api_models --load-plugins=pylint_plugins.db_models st2rbac_enterprise_backend_default/

.PHONY: .clone_st2_repo
.clone_st2_repo: /tmp/st2
/tmp/st2:
	@echo
	@echo "==================== cloning st2 repo ===================="
	@echo
	@rm -rf /tmp/st2
	@git clone https://github.com/StackStorm/st2.git --depth 1 --single-branch --branch $(ST2_REPO_BRANCH) $(ST2_REPO_PATH)

# NOTE: We pass --no-deps to the script so we don't install all the
# package dependencies which are already installed as part of "requirements"
# make targets. This speeds up the build
.PHONY: .install-runners
.install-runners:
	@echo ""
	@echo "================== install runners ===================="
	@echo ""
	@for component in $(COMPONENTS_RUNNERS); do \
		echo "==========================================================="; \
		echo "Installing runner:" $$component; \
		echo "==========================================================="; \
        (. $(VIRTUALENV_DIR)/bin/activate; cd $$component; python setup.py develop --no-deps); \
	done
	@echo ""
	@echo "================== register metrics drivers ======================"
	@echo ""

	# Install st2common to register metrics drivers
	(. $(VIRTUALENV_DIR)/bin/activate; cd $(ST2_REPO_PATH)/st2common; python setup.py develop --no-deps)

.PHONY: requirements
requirements: virtualenv .clone_st2_repo .install-runners
	@echo
	@echo "==================== requirements ===================="
	@echo
	. $(VIRTUALENV_DIR)/bin/activate && $(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache $(PIP_OPTIONS) -r /tmp/st2/requirements.txt
	. $(VIRTUALENV_DIR)/bin/activate && $(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache $(PIP_OPTIONS) -r /tmp/st2/test-requirements.txt

.PHONY: requirements-ci
requirements-ci:
	@echo
	@echo "==================== requirements-ci ===================="
	@echo
	. $(VIRTUALENV_DIR)/bin/activate && $(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache $(PIP_OPTIONS) -r /tmp/st2/requirements.txt
	. $(VIRTUALENV_DIR)/bin/activate && $(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache $(PIP_OPTIONS) -r /tmp/st2/test-requirements.txt

.PHONY: virtualenv
virtualenv: $(VIRTUALENV_DIR)/bin/activate
$(VIRTUALENV_DIR)/bin/activate:
	@echo
	@echo "==================== virtualenv ===================="
	@echo
	test -d $(VIRTUALENV_DIR) || virtualenv --no-site-packages $(VIRTUALENV_DIR)
