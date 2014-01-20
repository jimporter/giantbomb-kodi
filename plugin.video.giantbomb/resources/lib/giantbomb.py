import simplejson
import urllib
import urllib2

API_PATH = 'http://api.giantbomb.com'
DEFAULT_API_KEY = 'fa96542d69b4af7f31c2049ace5d89e84e225bef'

class GiantBomb(object):
    """A simple interface to the Giant Bomb API."""

    def __init__(self, api_key=None, on_update_api_key=None):
        """Create a new instance of the Giant Bomb API requester.

        :param api_key: The API key to use (or None to use the default)
        :param on_update_api_key: A function to call if the API key is changed
        """

        self.api_key = api_key or DEFAULT_API_KEY
        self.on_update_api_key = on_update_api_key

    def query(self, resource, query=None, format='json', retry=True):
        """Query the Giant Bomb API.

        :param resource: The resource to be queried
        :param query: A dict of the query arguments to pass to the resource
        :param format: The format to receive the response in
        :param retry: True if we should retry the query if the API key is bad
        :return: A dict with the response data from the API"""

        full_query = { 'api_key': self.api_key, 'format': format }
        if query:
            full_query.update(query)
        url = API_PATH + '/' + resource + '?' + urllib.urlencode(full_query)
        data = simplejson.loads(urllib2.urlopen(url).read())
        status = data.get('status_code', 1)

        if status == 1:
            return data
        else:
            if status == 100:
                self.api_key = DEFAULT_API_KEY
                if callable(self.on_update_api_key):
                    self.on_update_api_key(self.api_key)
                if retry:
                    return self.query(resource, query, format, retry=False)

            error_descrs = {
                100: 'Invalid API Key',
                101: 'Object Not Found',
                102: 'Error in URL Format',
                103: "'jsonp' format requires a 'json_callback' argument",
                104: 'Filter Error',
                105: 'Subscriber only video is for subscribers only',
                }
            descr = error_descrs.get(status,
                                     'Unknown Status Code {0}'.format(status))
            raise Exception(descr)

    def get_api_key(self, link_code):
        """Get the API key from the site given the link code.

        :param link_code: The link code received from the Giant Bomb website
        :return: The API key, or None if something went wrong
        """
        if link_code and len(link_code) == 6:
            data = self.query('validate', { 'link_code': link_code })
            if 'api_key' in data:
                self.api_key = data['api_key']
                if callable(self.on_update_api_key):
                    self.on_update_api_key(self.api_key)
                return self.api_key

        return None
