set -e

install_package() {
  PIP=/opt/stackstorm/st2/bin/pip
  WHEELSDIR=/opt/stackstorm/share/wheels
  ${PIP} install --find-links ${WHEELSDIR} --no-index --quiet --upgrade st2-enterprise-rbac-backend
}


enable_rbac() {
  crudini --set /etc/st2/st2.conf rbac enable 'True'
}

configure_rbac() {
  crudini --set /etc/st2/st2.conf rbac backend 'enterprise'
}

install_package

# NOTE: We only enable RBAC on initial installation. On upgrade we leave st2.conf alone.
# https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/#_syntax
#
#if [ "$1" -eq 1 ]; then
#  enable_rbac
#fi

# NOTE: Due to the bug in v3.0.0 where we incorrectly disable RBAC on upgrade we need to always
# enable RBAC - also on upgrade and not just on install otherwise users upgrading from v3.0.0
# would end up with RBAC disabled on upgrade.
# See https://github.com/StackStorm/st2-enterprise-rbac-backend/pull/13#issuecomment-495121941
# We can remove this and do it only on uprade in a future release- e.g. v3.2.0
enable_rbac
configure_rbac
