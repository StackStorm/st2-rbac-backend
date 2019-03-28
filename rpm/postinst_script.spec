set -e

enable_rbac() {
  crudini --set /etc/st2/st2.conf rbac enable 'True'
  crudini --set /etc/st2/st2.conf rbac backend 'enterprise'
}

enable_rbac
