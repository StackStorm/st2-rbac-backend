set -e

install_package() {
  PIP=/opt/stackstorm/st2/bin/pip
  WHEELSDIR=/opt/stackstorm/share/wheels
  ${PIP} install --find-links ${WHEELSDIR} --no-index --quiet --upgrade st2-enterprise-rbac-backend
}

# NOTE: This is a work around for a bug with RPM script introduced in v3.0.0.
# Because of a bug introduced in that issue Python package would get incorrectly
# removed on upgrade to a new version of that RPM package.
# As a workaround, we reinstall the package on %posttrans of new package which
# runs at the very end

install_package
