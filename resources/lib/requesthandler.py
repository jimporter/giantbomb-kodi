import re
import urllib
import urlparse

class RequestHandler(object):
    """A simple handler for requests against this plugin. To register handlers,
    use the handler and default_handler decorators."""
    def __init__(self, base_url):
        self._base_url = base_url
        self._mode_mapping = {}
        self._default_mode_mapping = None

    def handler(self, fn):
        self._mode_mapping[fn.__name__] = fn
        return fn

    def default_handler(self, fn):
        self._default_mode_mapping = fn
        return self.handler(fn)

    def build_url(self, query):
        """Build a URL to refer back to this add-on."""
        return self._base_url + '?' + urllib.urlencode(query)

    def run(self, arguments):
        params = dict(urlparse.parse_qsl( re.sub(r'^\?', '', arguments) ))
        mode = params.pop('mode', None)
        if mode is None:
            self._default_mode_mapping(**params)
        elif mode in self._mode_mapping:
            self._mode_mapping[mode](**params)
