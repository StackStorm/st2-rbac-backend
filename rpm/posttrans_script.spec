install_package() {
  PIP=/opt/stackstorm/st2/bin/pip
  WHEELSDIR=/opt/stackstorm/share/wheels

  # Only perform it if package is not installed so we don't run it twice on fresh install
  # and on upgrade
  ${PIP} list installed | grep st2-rbac-backend > /dev/null
  PIP_EXIT_CODE=$?
  which /opt/stackstorm/st2/bin/st2-apply-rbac-definitions > /dev/null 2>&1
  WHICH_EXIT_CODE=$?

  if [ ${PIP_EXIT_CODE} -eq 1 ] || [ ${WHICH_EXIT_CODE} -eq 1 ]; then
      # NOTE: We ignore errors (e.g. on uninstall when package doesn't exist on disk anymore)
      ${PIP} install --find-links ${WHEELSDIR} --no-index --quiet --upgrade --force-reinstall st2-rbac-backend || :
  fi
}

# NOTE: This is a work around for a bug with RPM script introduced in v3.0.0.
# Because of a bug introduced in that issue Python package would get incorrectly
# removed on upgrade to a new version of that RPM package.
# As a workaround, we reinstall the package on %posttrans of new package which
# runs at the very end
# This will result in double Python package installation on fresh install and
# upgrade, but that's harmless
# TODO: Remove this in v3.4.0
install_package
