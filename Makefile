ROOT_DIR ?= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
VIRTUALENV_DIR ?= virtualenv
ST2_REPO_PATH ?= /tmp/st2
ST2_REPO_BRANCH ?= master
FORCE_CHECK_ALL_FILES =? false
FORCE_CHECK_PACK =? false

export ST2_REPO_PATH ROOT_DIR

# All components are prefixed by st2
COMPONENTS := $(wildcard /tmp/st2/st2*)
COMPONENTS_RUNNERS := $(wildcard /tmp/st2/contrib/runners/*)

ifndef PYLINT_CONCURRENCY
	PYLINT_CONCURRENCY := 1
endif


.PHONY: all
all: requirements lint

.PHONY: all-ci
all-ci: compile .flake8 .pylint

.PHONY: lint
lint: requirements flake8 pylint configs-check metadata-check

.PHONY: flake8
flake8: requirements .flake8

.PHONY: pylint
pylint: requirements .clone_st2_repo .pylint

.PHONY: compile
compile:
	@echo "======================= compile ========================"
	@echo "------- Compile all .py files (syntax check test) ------"
	if python -c 'import compileall,re; compileall.compile_dir(".", rx=re.compile(r"/virtualenv|virtualenv-osx|virtualenv-py3|.tox|.git|.venv-st2devbox"), quiet=True)' | grep .; then exit 1; else exit 0; fi

.PHONY: .flake8
.flake8:
	@echo
	@echo "==================== flake8 ===================="
	@echo
	. $(VIRTUALENV_DIR)/bin/activate; flake8 --config=$(CI_DIR)/lint-configs/python/.flake8 st2rbac_enterprise_backend_default/

.PHONY: .pylint
.pylint:
	@echo
	@echo "==================== pylint ===================="
	@echo
	. $(VIRTUALENV_DIR)/bin/activate; pylint -j $(PYLINT_CONCURRENCY) -E --rcfile=./lint-configs/python/.pylintrc st2rbac_enterprise_backend_default/

.PHONY: .clone_st2_repo
.clone_st2_repo: /tmp/st2
/tmp/st2:
	@echo
	@echo "==================== cloning st2 repo ===================="
	@echo
	@rm -rf /tmp/st2
	@git clone https://github.com/StackStorm/st2.git --depth 1 --single-branch --branch $(ST2_REPO_BRANCH) /tmp/st2

.PHONY: .install-runners
.install-runners:
	@echo ""
	@echo "================== install runners ===================="
	@echo ""
	@for component in $(COMPONENTS_RUNNERS); do \
		echo "==========================================================="; \
		echo "Installing runner:" $$component; \
		echo "==========================================================="; \
        (. $(VIRTUALENV_DIR)/bin/activate; cd $$component; python setup.py develop); \
	done
	@echo ""
	@echo "================== register metrics drivers ======================"
	@echo ""

	# Install st2common to register metrics drivers
	(. $(VIRTUALENV_DIR)/bin/activate; cd $(ST2_REPO_PATH)/st2common; python setup.py develop)

.PHONY: requirements
requirements: virtualenv .clone_st2_repo .install-runners
	@echo
	@echo "==================== requirements ===================="
	@echo
	. $(VIRTUALENV_DIR)/bin/activate && $(VIRTUALENV_DIR)/bin/pip install --upgrade "pip>=9.0,<9.1"
	. $(VIRTUALENV_DIR)/bin/activate && $(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache -q -r /tmp/st2/requirements.txt
	. $(VIRTUALENV_DIR)/bin/activate && $(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache -q -r /tmp/st2/test-requirements.txt

.PHONY: requirements-ci
requirements-ci:
	@echo
	@echo "==================== requirements-ci ===================="
	@echo
	. $(VIRTUALENV_DIR)/bin/activate && $(VIRTUALENV_DIR)/bin/pip install --upgrade "pip>=9.0,<9.1"
	. $(VIRTUALENV_DIR)/bin/activate && $(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache -q -r /tmp/st2/requirements.txt
	. $(VIRTUALENV_DIR)/bin/activate && $(VIRTUALENV_DIR)/bin/pip install --cache-dir $(HOME)/.pip-cache -q -r /tmp/st2/test-requirements.txt

.PHONY: virtualenv
virtualenv: $(VIRTUALENV_DIR)/bin/activate
$(VIRTUALENV_DIR)/bin/activate:
	@echo
	@echo "==================== virtualenv ===================="
	@echo
	test -d $(VIRTUALENV_DIR) || virtualenv --no-site-packages $(VIRTUALENV_DIR)
