uninstall_package() {
  PIP=/opt/stackstorm/st2/bin/pip
  ${PIP} uninstall -y --quiet st2-enterprise-rbac-backend 1>/dev/null || :
}

disable_rbac() {
  crudini --del /etc/st2/st2.conf rbac enable
  crudini --del /etc/st2/st2.conf rbac backend
}

# 0 - uninstall
# 1 - upgrade
# See https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/#_syntax for details
if [ $1 -eq 0 ]; then
  uninstall_package
  disable_rbac
fi

# NOTE: We don't uninstall package on upgrade because during upgrade script
# ordering is as follows
#  %pre of new package
# (package install)
# %post of new package
# %preun of old package
# (removal of old package)
# %postun of old package
# This means that postun from the old package would remove files from new
# package because postun of old package runs after %post of new package
#if [ $1 -eq 1 ]; then
#  uninstall_package
#fi
