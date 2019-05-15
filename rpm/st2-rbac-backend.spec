%define pkg_version %(python setup.py --version 2>/dev/null)
%define version %(echo "${PKG_VERSION:-%{pkg_version}}")
#define epoch %(_epoch=`echo %{version} | grep -q dev || echo 1`; echo "${_epoch:-0}")
%define release %(echo "${PKG_RELEASE:-1}")
%define st2dir /opt/stackstorm
%define st2wheels %{st2dir}/share/wheels
%define pip %{st2dir}/st2/bin/pip

Name:           st2-rbac-backend
Version:        %{version}
%if 0%{?epoch}
Epoch: %{epoch}
%endif
Release:        %{release}
License:        Extreme Workflow Composer EULA
Summary:        RBAC Backend for EWC
URL:            https://www.extremenetworks.com/product/workflow-composer/
Source0:        st2-enterprise-rbac-backend

Requires: crudini st2

%define _builddir %(pwd)
%define _rpmdir %(pwd)/build

# Cat debian/package.links, set buildroot prefix and create symlinks.
%define debian_links cat debian/%{name}.links | grep -v '^\\s*#' | \
            sed -r -e 's~\\b~/~' -e 's~\\s+\\b~ %{buildroot}/~' | \
          while read link_rule; do \
            linkpath=$(echo "$link_rule" | cut -f2 -d' ') && [ -d $(dirname "$linkpath") ] || \
              mkdir -p $(dirname "$linkpath") && ln -s $link_rule \
          done \
%{nil}

%description
  RBAC Backend for Extreme Workflow Composer

%prep
  rm -rf %{buildroot}
  mkdir -p %{buildroot}

%build
  make

%install
  %debian_links
  %make_install

%clean
  rm -rf %{buildroot}

%post
  %include rpm/postinst_script.spec

%postun
  %include rpm/postun_script.spec

%files
  %doc rpm/LICENSE
  %{_bindir}/*
  %{st2wheels}/*
