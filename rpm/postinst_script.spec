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
if [ "$1" -eq 1 ]; then
  enable_rbac
fi

configure_rbac
