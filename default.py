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
DEFAULT_API_KEY = 'fa96542d69b4af7f31c2049ace5d89e84e225bef'
API_KEY = DEFAULT_API_KEY
addon_id = int(sys.argv[1])
my_addon = xbmcaddon.Addon('plugin.video.giantbombex')

def dump(s):
    print '[GB2] ' + str(s)

def query_api(resource, query=None, format='json'):
    """Query the Giant Bomb API."""
    full_query = { 'api_key': API_KEY, 'format': format }
    if (query):
        full_query.update(query)
    url = API_PATH + '/' + resource + '?' + urllib.urlencode(full_query)
    data = simplejson.loads(urllib2.urlopen(url).read())

    if data.get('status_code', 1) == 100:
        dump('Warning! Bad API key detected. Resetting the key and retrying.')
        global API_KEY
        API_KEY = DEFAULT_API_KEY
        my_addon.setSetting('api_key', '')
        data = simplejson.loads(urllib2.urlopen(url).read())

    return data

def get_api_key(link_code):
    """Get the API key from the site given the link code."""
    if link_code and len(link_code) == 6:
        data = query_api('validate', { 'link_code': link_code })
        if data.get('api_key'):
            global API_KEY
            API_KEY = data['api_key']
            my_addon.setSetting('api_key', data['api_key'])
            return True
    return False

class RequestHandler(object):
    """A simple handler for requests against this plugin. To register handlers,
    use the handler and default_handler decorators."""
    def __init__(self):
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
        return sys.argv[0] + '?' + urllib.urlencode(query)

    def run(self, arguments):
        params = dict(urlparse.parse_qsl( re.sub(r'^\?', '', arguments) ))
        mode = params.get('mode')
        if mode is None:
            self._default_mode_mapping(**params)
        elif mode in self._mode_mapping:
            self._mode_mapping[mode](**params)

handler = RequestHandler()

@handler.handler
def link_account(first_run=False, **kwargs):
    dialog = xbmcgui.Dialog()
    nolabel = 'Skip' if first_run else 'Cancel'
    ok = dialog.yesno("Let's do this.",
                      'To link your account, visit',
                      'www.giantbomb.com/xbmc to get a link code.',
                      'Enter this code on the next screen.',
                      yeslabel='Next', nolabel=nolabel)

    while ok:
        keyboard = xbmc.Keyboard('', 'Enter your link code', False)
        keyboard.doModal()
        if keyboard.isConfirmed():
            link_code = keyboard.getText().upper()
            if get_api_key(link_code):
                dialog.ok('Success!', 'Your account is now linked!',
                          'If you are a premium member,',
                          'you should now have premium privileges.')
                return True
            else:
                ok = dialog.yesno("We're really sorry, but...",
                                  'We could not link your account.',
                                  'Make sure the code you entered is correct',
                                  'and try again.',
                                  yeslabel='Try again', nolabel='Cancel')
        else:
            ok = False

    # If we got here, we gave up trying to link the account.
    return False

@handler.handler
def unlink_account(**kwargs):
    dialog = xbmcgui.Dialog()
    ok = dialog.yesno('Oh no!',
                      'Are you sure you want to unlink your account?',
                      yeslabel='Unlink', nolabel='Cancel')
    if ok:
        my_addon.setSetting('api_key', '')

@handler.default_handler
def categories(**kwargs):
    if my_addon.getSetting('first_run') == 'true':
        if not my_addon.getSetting('api_key'):
            link_account(first_run=True)
        my_addon.setSetting('first_run', 'false')

    data = query_api('video_types')
    total = data['number_of_total_results'] + 1 # Add one for "Search"
    for category in data['results']:
        name = category['name']
        mode = 'endurance' if category['id'] == 5 else 'videos'
        url = handler.build_url({ 'mode': mode, 'video_type': category['id'] })
        li = xbmcgui.ListItem(category['name'], iconImage='DefaultFolder.png')

        xbmcplugin.addDirectoryItem(handle=addon_id, url=url,
                                    listitem=li, isFolder=True,
                                    totalItems=total)

    url = handler.build_url({ 'mode': 'search' })
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
        url = handler.build_url({ 'page': page-1 }.extend(extraargs))
        menu.append(('Previous page', 'Container.Update(' + url + ', replace)'))
    if (page+1) * 100 < total:
        url = handler.build_url({ 'page': page+1 }.extend(extraargs))
        menu.append(('Next page', 'Container.Update(' + url + ', replace)'))

    for video in data['results']:
        name = video['name']
        remote_url = video['high_url']
        url = handler.build_url({ 'mode': 'play', 'url': remote_url })
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

@handler.handler
def videos(video_type, page='0', gb_filter=None, **kwargs):
    page = int(page)
    api_params = { 'video_type': video_type, 'offset': page*100 }
    plugin_params = { 'mode': 'videos', 'video_type': video_type }
    if gb_filter:
        api_params['filter'] = gb_filter
        plugin_params['gb_filter'] = gb_filter
    data = query_api('videos', api_params)
    list_videos(data, page, plugin_params)

@handler.handler
def endurance(**kwargs):
    runs = [ 'Chrono Trigger', 'Deadly Premonition', 'Persona 4',
             'The Matrix Online' ]

    for run in runs:
        url = handler.build_url({ 'mode': 'videos', 'video_type': '5',
                                  'gb_filter': 'name:' + run })
        li = xbmcgui.ListItem(run, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_id, url=url,
                                    listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_id)

@handler.handler
def search(query=None, page='0', **kwargs):
    page = int(page)

    if query is None:
        keyboard = xbmc.Keyboard('', 'Search', False)
        keyboard.doModal()
        if keyboard.isConfirmed():
            query = keyboard.getText()
        else:
            xbmc.executebuiltin('Action(ParentDir)')
            return

    data = query_api('search', { 'resources': 'video', 'query': query,
                                 'offset': page*100})
    list_videos(data, page, { 'mode': 'search', 'query': query })

@handler.handler
def play(url, **kwargs):
    li = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(addon_id, True, li)

if my_addon.getSetting('api_key'):
    API_KEY = my_addon.getSetting('api_key')

xbmcplugin.setContent(addon_id, 'movies')
xbmcplugin.setPluginFanart(addon_id, my_addon.getAddonInfo('fanart'))

handler.run(sys.argv[2])
