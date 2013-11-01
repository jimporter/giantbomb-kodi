Giant Bomb for XBMC
===================

This is an add-on for XBMC to show the latest and greatest videos from Giant
Bomb dot com (a website about video games, and a video game website).

Development
-----------

The actual source for the add-on is in `plugin.video.giantbomb/`. To make
development easier, there are `make` commands to install/uninstall the add-on
from your local XBMC instance:

```
make install-dev
make uninstall-dev
```

Testing
-------

Tests are located in `tests/` (big surprise there). You can (and should!) run
them from `make`:

```
make test
```

Packaging
---------

To package the add-on into a .zip file for release, just run:

```
make package
```