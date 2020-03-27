# Copyright (C) 2019 Extreme Networks, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

ROOT_DIR ?= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

PKG_NAME := st2-rbac-backend
PKG_RELEASE ?= 1
WHEELSDIR ?= opt/stackstorm/share/wheels
VIRTUALENV_DIR ?= virtualenv
ST2_REPO_PATH ?= /tmp/st2
ST2_REPO_URL ?= git@github.com:StackStorm/st2.git
ST2_REPO_BRANCH ?= master

ifneq (,$(wildcard /etc/debian_version))
	DEBIAN := 1
	DEB_DISTRO := $(shell lsb_release -cs)
else
	REDHAT := 1
	DEB_DISTRO := unstable
endif

ifeq ($(DEB_DISTRO),bionic)
	PYTHON_BINARY := /usr/bin/python3
	PIP_BINARY := /usr/local/bin/pip3
else
	PYTHON_BINARY := python
	PIP_BINARY := pip
endif

# NOTE: We remove trailing "0" which is added at the end by newer versions of pip
# For example: 3.0.dev0 -> 3.0.dev
PKG_VERSION := $(shell $(PYTHON_BINARY) setup.py --version 2> /dev/null | sed 's/\.dev[0-9]$$/dev/')
CHANGELOG_COMMENT ?= "automated build, version: $(PKG_VERSION)"

# nasty hack to get a space into a variable
colon := :
comma := ,
dot := .
slash := /
space_char :=
space_char +=

# All components are prefixed by st2
COMPONENTS = $(wildcard $(ST2_REPO_PATH)/st2*)
COMPONENTS_RUNNERS := $(wildcard $(ST2_REPO_PATH)/contrib/runners/*)
COMPONENTS_WITH_RUNNERS := $(COMPONENTS) $(COMPONENTS_RUNNERS)
COMPONENT_PYTHONPATH = $(subst $(space_char),:,$(realpath $(COMPONENTS_WITH_RUNNERS))):$(ST2_REPO_PATH)
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
	@echo "DEBIAN=$(DEBIAN)"
	@echo "REDHAT=$(REDHAT)"
	@echo "DEB_DISTRO=$(DEB_DISTRO)"
	@echo "PYTHON_BINARY=$(PYTHON_BINARY)"
	@echo "PIP_BINARY=$(PIP_BINARY)"
	@echo "PKG_VERSION=$(PKG_VERSION)"
	@echo "PKG_RELEASE=$(PKG_RELEASE)"
	@echo
	@echo COMPONENTS=$(COMPONENTS)
	@echo COMPONENTS_RUNNERS=$(COMPONENTS_RUNNERS)
	@echo COMPONENTS_WITH_RUNNERS=$(COMPONENTS_WITH_RUNNERS)
	@echo COMPONENT_PYTHONPATH=$(COMPONENT_PYTHONPATH)
	@echo TRAVIS_PULL_REQUEST=$(TRAVIS_PULL_REQUEST)
	@echo NOSE_OPTS=$(NOSE_OPTS)
	@echo

.PHONY: all
all: requirements lint

.PHONY: all-ci
all-ci: compile .flake8 .pylint

.PHONY: lint
lint: requirements flake8 pylint

.PHONY: .lint
.lint: compile .flake8 .pylint

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
	. $(VIRTUALENV_DIR)/bin/activate; flake8 --config=lint-configs/python/.flake8-proprietary st2rbac_enterprise_backend/ tests/

.PHONY: .pylint
.pylint:
	@echo
	@echo "==================== pylint ===================="
	@echo
	. $(VIRTUALENV_DIR)/bin/activate; pylint -j $(PYLINT_CONCURRENCY) -E --rcfile=./lint-configs/python/.pylintrc --load-plugins=pylint_plugins.api_models --load-plugins=pylint_plugins.db_models st2rbac_enterprise_backend/

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
	NOSE_WITH_TIMER=$(NOSE_WITH_TIMER) tox -e py36-unit -vv

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
        (. $(VIRTUALENV_DIR)/bin/activate; cd $$component; python setup.py develop --no-deps); \
	done
	@echo ""
	@echo "================== register metrics drivers ======================"
	@echo ""

	# Install st2common to register metrics drivers
	(. $(VIRTUALENV_DIR)/bin/activate; cd $(ST2_REPO_PATH)/st2common; python setup.py develop --no-deps)

	@echo ""
	@echo "================== register rbac backend ======================"
	@echo ""
	(. $(VIRTUALENV_DIR)/bin/activate; python setup.py develop --no-deps)


.PHONY: requirements
requirements: virtualenv .clone_st2_repo .install-runners-and-deps
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
	test -d $(VIRTUALENV_DIR) || virtualenv $(VIRTUALENV_DIR)

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

# Package build tasks
.PHONY: all install install_wheel install_deps deb rpm
all:

install: install_wheel install_deps

install_wheel:
	install -d $(DESTDIR)/$(WHEELSDIR)
	$(PYTHON_BINARY) setup.py bdist_wheel -d $(DESTDIR)/$(WHEELSDIR)

# This step is arch-dependent and must be called only on prepared environment,
# it's run inside stackstorm/buildpack containers.
install_deps:
	$(PIP_BINARY) wheel --wheel-dir=$(DESTDIR)/$(WHEELSDIR) -r requirements.txt
	# Well welcome to enterprise (rhel).
	# Hardcore workaround to make wheel installable on any platform.
	cd $(DESTDIR)/$(WHEELSDIR); \
		ls -1 *-cp27mu-*.whl | while read f; do \
			mv $$f $$(echo $$f | sed "s/cp27mu/none/"); \
		done

deb:
	[ -z "$(DEB_EPOCH)" ] && _epoch="" || _epoch="$(DEB_EPOCH):"; \
		dch -m --force-distribution -v$${_epoch}$(PKG_VERSION)-$(PKG_RELEASE) -D$(DEB_DISTRO) $(CHANGELOG_COMMENT)
	dpkg-buildpackage -b -uc -us -j`_cpunum=$$(nproc); echo "${_cpunum:-1}"`

rpm:
	rpmbuild -bb rpm/st2-rbac-backend.spec
