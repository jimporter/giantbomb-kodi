import urllib2
import xml.etree.ElementTree

namespaces = { 'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd' }


class RSSParser(object):
    """A simple class to parse RSS feeds."""

    def __init__(self, url):
        """Create a new RSS parser.

        :param url: The URL for the RSS feed."""

        f = urllib2.urlopen(url)
        self._tree = xml.etree.ElementTree.parse(f)
        f.close()

    @property
    def title(self):
        """Get the feed's title.

        :return: The feed's title or None if no title exists."""

        return self._try_get_text(self._tree, 'channel/title')

    @property
    def image(self):
        """Get the feed's image.

        :return: The feed's image as a dict or None if no image exists."""

        image = self._tree.find('channel/image')
        if image:
            return {
                'title':  self._try_get_text(image, 'title'),
                'url':    self._try_get_text(image, 'url'),
                'link':   self._try_get_text(image, 'link'),
                'width':  self._try_get_text(image, 'width'),
                'height': self._try_get_text(image, 'height'),
            }

    @property
    def items(self):
        """Iterate over all items in the RSS feed."""

        for item in self._tree.findall('channel/item'):
            yield {
                'title':       self._try_get_text(item, 'title'),
                'description': self._try_get_text(item, 'description'),
                'date':        self._try_get_text(item, 'pubDate'),
                'author':      self._try_get_text(item, 'itunes:author'),
                'image':       self._try_get_attr(item, 'itunes:image',
                                                  'href'),
                'url':         self._try_get_attr(item, 'enclosure', 'url'),
                'length':      self._try_get_attr(item, 'enclosure', 'length'),
            }

    def _try_get_text(self, node, path, default=None):
        child = node.find(path, namespaces=namespaces)
        if child is not None:
            return child.text
        else:
            return default

    def _try_get_attr(self, node, path, attr, default=None):
        child = node.find(path, namespaces=namespaces)
        if child is not None:
            return child.get(attr, default)
        else:
            return default
