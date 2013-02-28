import re
import urllib
import urllib2
import urlparse
import simplejson
import xbmcaddon
import xbmcplugin
import xbmcgui
import time

API_PATH = 'http://api.giantbomb.com'
API_KEY = 'fa96542d69b4af7f31c2049ace5d89e84e225bef' # Default API key
addon_id = int(sys.argv[1])
my_addon = xbmcaddon.Addon('plugin.video.giantbomb2')

def dump(s):
    print '[GB2] ' + str(s)

def query_api(resource, query=None, format='json'):
    """Query the Giant Bomb API."""
    full_query = { 'api_key': API_KEY, 'format': format }
    if (query):
        full_query.update(query)
    url = API_PATH + '/' + resource + '?' + urllib.urlencode(full_query)
    response = urllib2.urlopen(url)
    return simplejson.loads(response.read())

def build_url(query):
    """Build a URL to refer back to this add-on."""
    return sys.argv[0] + '?' + urllib.urlencode(query)

class Plugin(object):
    """A simple handler for requests against this plugin. To register handlers,
    use the handler and default_handler decorators."""
    def __init__(self):
        self._mode_mapping = {}
        self._default_mode_mapping = None

    def handler(self, fn):
        self._mode_mapping[fn.__name__] = fn

    def default_handler(self, fn):
        self._default_mode_mapping = fn
        self.handler(fn)

    def run(self, arguments):
        params = dict(urlparse.parse_qsl( re.sub(r'^\?', '', arguments) ))
        mode = params.get('mode')
        if mode is None:
            self._default_mode_mapping(**params)
        elif mode in self._mode_mapping:
            self._mode_mapping[mode](**params)

plugin = Plugin()

@plugin.default_handler
def categories(**kwargs):
    data = query_api('video_types')
    total = data['number_of_total_results'] + 1 # Add one for "Search"
    for category in data['results']:
        name = category['name']
        mode = 'endurance' if category['id'] == 5 else 'videos'
        url = build_url({ 'mode': mode, 'video_type': category['id'] })
        li = xbmcgui.ListItem(category['name'], iconImage='DefaultFolder.png')

        xbmcplugin.addDirectoryItem(handle=addon_id, url=url,
                                    listitem=li, isFolder=True,
                                    totalItems=total)

    url = build_url({ 'mode': 'search' })
    li = xbmcgui.ListItem('Search', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_id, url=url,
                                listitem=li, isFolder=True,
                                totalItems=total)
    xbmcplugin.endOfDirectory(addon_id)

def list_videos(data, page, extraargs):
    xbmcplugin.addSortMethod(addon_id, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(addon_id, xbmcplugin.SORT_METHOD_TITLE)

    total = data['number_of_total_results']

    menu = []
    if page != 0:
        url = build_url({ 'page': page-1 }.extend(extraargs))
        menu.append(('Previous page', 'Container.Update(' + url + ', replace)'))
    if (page+1) * 100 < total:
        url = build_url({ 'page': page+1 }.extend(extraargs))
        menu.append(('Next page', 'Container.Update(' + url + ', replace)'))

    for video in data['results']:
        name = video['name']
        remote_url = video['high_url']
        url = build_url({ 'mode': 'play', 'url': remote_url })
        date = time.strptime(video['publish_date'], '%Y-%m-%d %H:%M:%S')
        duration = video['length_seconds']

        li = xbmcgui.ListItem(name, iconImage='DefaultVideo.png',
                              thumbnailImage=video['image']['super_url'])
        li.addStreamInfo('video', { 'duration': duration })
        li.setInfo('video', infoLabels={
                'title': name,
                'plot': video['deck'],
                'date': time.strftime('%d.%m.%Y', date),
                })
        li.setProperty('IsPlayable', 'true')
        li.addContextMenuItems(menu)
        xbmcplugin.addDirectoryItem(handle=addon_id, url=url,
                                    listitem=li, totalItems=total)

    xbmcplugin.endOfDirectory(addon_id)

@plugin.handler
def videos(video_type, page='0', gb_filter=None, **kwargs):
    page = int(page)
    api_params = { 'video_type': video_type, 'offset': page*100 }
    plugin_params = { 'mode': 'videos', 'video_type': video_type }
    if gb_filter:
        api_params['filter'] = gb_filter
        plugin_params['gb_filter'] = gb_filter
    data = query_api('videos', api_params)
    list_videos(data, page, plugin_params)

@plugin.handler
def endurance(**kwargs):
    runs = [ 'Chrono Trigger', 'Deadly Premonition', 'Persona 4',
             'The Matrix Online' ]

    for run in runs:
        url = build_url({ 'mode': 'videos', 'video_type': '5',
                          'gb_filter': 'name:' + run })
        li = xbmcgui.ListItem(run, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_id, url=url,
                                    listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_id)

@plugin.handler
def search(query=None, page='0', **kwargs):
    page = int(page)

    if query is None:
        keyboard = xbmc.Keyboard('', 'Search', False)
        keyboard.doModal()
        if keyboard.isConfirmed():
            query = keyboard.getText()
        else:
            return categories() # XXX: Find a "go back" command?

    data = query_api('search', { 'resources': 'video', 'query': query,
                                 'offset': page*100})
    list_videos(data, page, { 'mode': 'search', 'query': query })

@plugin.handler
def play(url, **kwargs):
    li = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(addon_id, True, li)


xbmcplugin.setContent(addon_id, 'movies')
xbmcplugin.setPluginFanart(addon_id, my_addon.getAddonInfo('fanart'))

plugin.run(sys.argv[2])
