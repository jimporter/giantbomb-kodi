[![GitHub release][release-image]][release-link]

Giant Bomb for Kodi
===================

This is an add-on for Kodi (aka XBMC) to show the latest and greatest videos
from Giant Bomb dot com.

Giant Bomb dot com? What's that?
--------------------------------

It's a website. About video games.

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

Tests are located in `test/` (big surprise there). You can (and should!) run
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

License
-------

This add-on is licensed under the GPL, version 3.

Credits
-------

Image files (and a few small vestiges of code) courtesy of
[Whiskey Media](https://github.com/WhiskeyMedia/xbmc).

[release-image]: https://img.shields.io/github/release/jimporter/giantbomb-kodi.svg?style=flat
[release-link]: https://github.com/jimporter/giantbomb-kodi/releases