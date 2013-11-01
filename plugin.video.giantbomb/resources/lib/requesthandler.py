import re
import urllib
import urlparse

class RequestHandler(object):
    """A simple handler for requests against this plugin. To register handlers,
    use the handler and default_handler decorators."""

    def __init__(self, base_url):
        """Create a new request handler.

        :param base_url: The base URL of the add-on (usually sys.argv[0])
        """

        self._base_url = base_url
        self._mode_mapping = {}
        self._default_mode_mapping = None

    def handler(self, fn):
        """A decorator to use for declaring a function as handling a particular
        mode for this add-on.

        :param fn: The function to decorate
        :return: The decorated function
        """

        self._mode_mapping[fn.__name__] = fn
        return fn

    def default_handler(self, fn):
        """A decorator to use for declaring a function as being the default
        handler for this add-on (as well as a regular handler; see above).

        :param fn: The function to decorate
        :return: The decorated function
        """

        self._default_mode_mapping = fn
        return self.handler(fn)

    def build_url(self, query):
        """Build a URL to refer back to this add-on.

        :param query: A dict of the query arguments for the URL
        :return: The built URL"""

        return self._base_url + '?' + urllib.urlencode(query)

    def run(self, arguments):
        """Run the request handler and dispatch to the appropiate handler
        function, as registered by RequestHandler.handler or
        RequestHandler.default_handler.

        :param arguments: The arguments to the add-on (usually sys.argv[2])"""

        params = dict(urlparse.parse_qsl( re.sub(r'^\?', '', arguments) ))
        mode = params.pop('mode', None)
        if mode is None:
            self._default_mode_mapping(**params)
        elif mode in self._mode_mapping:
            self._mode_mapping[mode](**params)
