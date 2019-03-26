# StackStorm Enterprise RBAC Backend for StackStorm Enterprise Edition

StackStorm RBAC backend for enterprise version which contains all the proprietary RBAC
(permission resolving) business logic.

NOTE: Due to the original code structure and code originally living as part of the
open source StackStorm/st2 repo, some of the utility RBAC code is still part of the open
source repo (that code is of little use without the permission resolving classes which
contain majority of the business logic though).

## Installation

NOTE: This happens automatically as part of the bwc-enterprise package post install step.

1. Make sure the backend Python package is installed inside StackStorm virtualenv
   (``/opt/stackstorm/st2/``)
2: Edit StackStorm config (``/etc/st2/st2.conf``):

```ini
...
[rbac]
enable = True
backend = enterprise
...
3. Restart all the services - ``sudo st2ctl restart``
