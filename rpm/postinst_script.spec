set -e

install_pacakge() {
  PIP=/opt/stackstorm/st2/bin/pip
  WHEELSDIR=/opt/stackstorm/share/wheels
  ${PIP} install --find-links ${WHEELSDIR} --no-index --quiet --upgrade st2-enterprise-rbac-backend
}
enable_rbac() {
  crudini --set /etc/st2/st2.conf rbac enable 'True'
  crudini --set /etc/st2/st2.conf rbac backend 'enterprise'
}

install_pacakge
enable_rbac
