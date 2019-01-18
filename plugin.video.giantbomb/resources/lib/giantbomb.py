import json
import urllib
import urllib2

class APIError(Exception):
    """An error for when the Giant Bomb API doesn't like something we did."""

    error_descs = {
        100: 'Invalid API Key',
        101: 'Object Not Found',
        102: 'Error in URL Format',
        103: "'jsonp' format requires a 'json_callback' argument",
        104: 'Filter Error',
        105: 'Subscriber only video is for subscribers only',
        107: 'Rate limit exceeded',
    }

    def __init__(self, status):
        """Create a new Giant Bomb API error.

        :param status: The status code from the API response"""

        Exception.__init__(self, self.error_descs.get(
            status, 'Unknown Status Code {0}'.format(status)
        ))
        self.status = status

class GiantBomb(object):
    """A simple interface to the Giant Bomb API."""

    api_path_template = '{protocol}://www.giantbomb.com/api'
    default_api_key = 'fa96542d69b4af7f31c2049ace5d89e84e225bef'

    def __init__(self, api_key=None, on_update_api_key=None, https=True):
        """Create a new instance of the Giant Bomb API requester.

        :param api_key: The API key to use (or None to use the default)
        :param on_update_api_key: A function to call if the API key is changed
        :param https: True if we should use HTTPS, False otherwise
        """

        self.api_key = api_key or self.default_api_key
        self.on_update_api_key = on_update_api_key
        self.api_path = self.api_path_template.format(
            protocol='https' if https else 'http'
        )

    def get_api_key(self, link_code):
        """Get the API key from the site given the link code.

        :param link_code: The link code received from the Giant Bomb website
        :return: The API key, or None if something went wrong"""

        if link_code and len(link_code) == 6:
            data = self.query('validate', { 'link_code': link_code })
            if 'api_key' in data:
                self.api_key = data['api_key']
                if callable(self.on_update_api_key):
                    self.on_update_api_key(self.api_key)
                return self.api_key

        return None

    def query(self, resource, query=None, format='json', retry=True):
        """Query the Giant Bomb API for a particular resource.

        :param resource: The resource to be queried
        :param query: A dict of the query arguments to pass to the resource
        :param format: The format to receive the response in
        :param retry: True if we should retry the query if the API key is bad
        :return: A dict with the response data from the API"""

        full_query = { 'api_key': self.api_key, 'format': format }
        if query:
            full_query.update(query)

        return self.fetch('{base}/{resource}?{query}'.format(
            base=self.api_path,
            resource=resource,
            query=urllib.urlencode(full_query),
        ), retry=retry)

    def fetch(self, url, retry=True):
        """Fetch a pre-built URL from the Giant Bomb API.

        :param url: The URL to fetch
        :param retry: True if we should retry the query if the API key is bad
        :return: A dict with the response data from the API"""

        try:
            return self._do_fetch(url)
        except APIError as e:
            if retry and e.status == 100:
                self._reset_api_key()
                return self._do_fetch(url)
            raise

    def _reset_api_key(self):
        """Reset the API key (e.g. when the API tells us our key is bad)."""

        self.api_key = self.default_api_key
        if callable(self.on_update_api_key):
            self.on_update_api_key(self.api_key)

    def _do_fetch(self, url):
        """Fetch a URL from the Giant Bomb API.

        :param url: The URL to fetch
        :return: A dict with the response data from the API"""

        data = json.loads(urllib2.urlopen(url).read())
        status = data.get('status_code', 1)

        if status == 1:
            return data
        raise APIError(status)

_realnames = {
    'alex':          'Alex Navarro',
    'brad':          'Brad Shoemaker',
    'danryckert':    'Dan Ryckert',
    'drewbert':      'Drew Scanlon',
    'jeff':          'Jeff Gerstmann',
    'marino':        "Brad 'Marino' Lynch",
    'mattbodega':    'Matt Kessler',
    'patrickklepek': 'Patrick Klepek',
    'perryvandell':  'Perry Vandell',
    'rorie':         'Matt Rorie',
    'ryan':          'Ryan Davis',
    'snide':         'Dave Snider',
    'unastrike':     'Jason Oestreicher',
    'vinny':         'Vinny Caravella',
    'zacminor':      'Zac Minor',
}
def map_usernames(names):
    """Map the Giant Bomb crew's usernames to their real names.

    :param names: A string (separated by ', ') of usernames
    :return: A string of real names"""

    if not names:
        return None
    return ', '.join(_realnames.get(i, i) for i in names.split(', '))
