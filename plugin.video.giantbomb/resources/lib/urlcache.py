import os
import time
import urllib


def _trymakedirs(path, mode=0777):
    """Try to recursively create directories using os.makedirs. If the directory
    already exists, do nothing. This is equivalent to
    os.makedirs(path, mode, exist_ok=True) in Python 3.2+.

    :param path: The path to create.
    :param mode: The directory's mode."""
    try:
        os.makedirs(path)
    except OSError, e:
        if e.errno != 17 or not os.path.isdir(path):
            raise


class URLCache(object):
    """A simple class to cache the contents of URLs by an arbitrary id."""

    def __init__(self, basepath, expiry_secs=86400):
        """Create a new URL cache.

        :param basepath: The root directory to cache the URLs in.
        :param expiry_secs: The time in seconds until a cached URL expires."""

        self._basepath = basepath
        self._expiry_secs = expiry_secs

    def __contains__(self, item):
        """Check if an item is cached.

        :param item: The item id.
        :return: True if the item is in the cache; false otherwise."""

        path = os.path.join(self._basepath, item)
        return os.path.exists(path)

    def __getitem__(self, item):
        """Get an item out of the cache, as a local filename.

        :param item: The item id.
        :return: The filename for the item; throws KeyError if the file doesn't
                 exist."""

        path = os.path.join(self._basepath, item)
        if not os.path.exists(path):
            raise KeyError
        return path

    def get(self, item, default=None):
        """Get an item out of the cache, as a local filename.

        :param item: The item id.
        :param default: A value to return if the item isn't cached.
        :return: The filename for the item; return `default` if the file
                 doesn't exist."""

        try:
            return self[item]
        except Exception:
            return default

    def __setitem__(self, item, url):
        """Put an item in the cache; this does nothing if the item is already
        cached and hasn't expired yet.

        :param item: The item id.
        :param url: The URL to cache."""

        path = os.path.join(self._basepath, item)
        if ( not os.path.exists(path) or
             os.path.getmtime(path) + self._expiry_secs < time.time() ):
            _trymakedirs(self._basepath)
            urllib.urlretrieve(url, path)

    def __delitem__(self, item):
        """Remove an item from the cache.

        :param item: The item id."""

        path = os.path.join(self._basepath, item)
        os.remove(path)
