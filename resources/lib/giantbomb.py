import simplejson
import urllib
import urllib2

API_PATH = 'http://api.giantbomb.com'
DEFAULT_API_KEY = 'fa96542d69b4af7f31c2049ace5d89e84e225bef'

class GiantBomb(object):
    def __init__(self, api_key=None, on_update_api_key=None):
        self.api_key = api_key or DEFAULT_API_KEY
        self.on_update_api_key = on_update_api_key

    def query(self, resource, query=None, format='json', retry=True):
        """Query the Giant Bomb API."""
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
            raise Exception('failure') # XXX stringify this

    def get_api_key(self, link_code):
        """Get the API key from the site given the link code."""
        if link_code and len(link_code) == 6:
            data = query_api('validate', { 'link_code': link_code })
            if 'api_key' in data:
                self.api_key = data['api_key']
                if callable(self.on_update_api_key):
                    self.on_update_api_key(self.api_key)
                return self.api_key

        return None
