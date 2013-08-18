import re
import simplejson
import time
import urllib
import urllib2
import urlparse
import xbmcaddon
import xbmcplugin
import xbmcgui

API_PATH = 'http://api.giantbomb.com'
DEFAULT_API_KEY = 'fa96542d69b4af7f31c2049ace5d89e84e225bef'
API_KEY = DEFAULT_API_KEY
addon_id = int(sys.argv[1])
my_addon = xbmcaddon.Addon('plugin.video.giantbomb')

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
        mode = params.pop('mode', None)
        if mode is None:
            self._default_mode_mapping(**params)
        elif mode in self._mode_mapping:
            self._mode_mapping[mode](**params)

handler = RequestHandler()

@handler.handler
def link_account(first_run=False):
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
def unlink_account():
    dialog = xbmcgui.Dialog()
    ok = dialog.yesno('Oh no!',
                      'Are you sure you want to unlink your account?',
                      yeslabel='Unlink', nolabel='Cancel')
    if ok:
        my_addon.setSetting('api_key', '')

@handler.default_handler
def categories():
    if my_addon.getSetting('first_run') == 'true':
        if not my_addon.getSetting('api_key'):
            link_account(first_run=True)
        my_addon.setSetting('first_run', 'false')

    data = query_api('video_types')
    # Count up the total number of categories; add one for "Latest" and one more
    # for "Search".
    total = data['number_of_total_results'] + 2

    # Add the "Latest" pseudo-category
    url = handler.build_url({ 'mode': 'videos' })
    li = xbmcgui.ListItem('Latest', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_id, url=url,
                                listitem=li, isFolder=True,
                                totalItems=total)

    # Add all the real categories
    for category in data['results']:
        name = category['name']
        mode = 'endurance' if category['id'] == 5 else 'videos'
        url = handler.build_url({
                'mode': mode,
                'gb_filter': 'video_type:%d' % category['id']
                })
        li = xbmcgui.ListItem(category['name'], iconImage='DefaultFolder.png')

        xbmcplugin.addDirectoryItem(handle=addon_id, url=url,
                                    listitem=li, isFolder=True,
                                    totalItems=total)

    # Add the "Search" pseudo-category
    url = handler.build_url({ 'mode': 'search' })
    li = xbmcgui.ListItem('Search', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_id, url=url,
                                listitem=li, isFolder=True,
                                totalItems=total)
    xbmcplugin.endOfDirectory(addon_id)

def list_videos(data, page, plugin_params=None):
    xbmcplugin.addSortMethod(addon_id, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(addon_id, xbmcplugin.SORT_METHOD_TITLE)

    quality_mapping = ['low_url', 'high_url', 'hd_url']
    quality = quality_mapping[ int(my_addon.getSetting('video_quality')) ]

    menu = []

    total = data['number_of_total_results']
    if page == 'all':
        this_page = total
    else:
        this_page = len(data['results'])

        if page > 0:
            url = handler.build_url(dict(page=page-1, **plugin_params))
            menu.append(('Previous page',
                         'Container.Update(' + url + ', replace)'))
        if (page+1) * 100 < total:
            url = handler.build_url(dict(page=page+1, **plugin_params))
            menu.append(('Next page', 'Container.Update(' + url + ', replace)'))

    for video in data['results']:
        name = video['name']
        date = time.strptime(video['publish_date'], '%Y-%m-%d %H:%M:%S')
        duration = video['length_seconds']

        # Build the URL for playing the video
        remote_url = video.get(quality, video['high_url'])
        if quality == 'hd_url' and 'hd_url' in video:
            # XXX: This assumes the URL already has a query string!
            remote_url += '&' + urllib.urlencode({ 'api_key': API_KEY })
        url = handler.build_url({ 'mode': 'play', 'url': remote_url })

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
                                    listitem=li, totalItems=this_page)

@handler.handler
def videos(gb_filter=None, page='0'):
    api_params = {}
    plugin_params = { 'mode': 'videos' }

    if gb_filter:
        api_params['filter'] = plugin_params['gb_filter'] = gb_filter

    if page == 'all':
        data = query_api('videos', api_params)
        list_videos(data, page, plugin_params)
        total = data['number_of_total_results']

        for offset in range(100, total, 100):
            api_params['offset'] = offset
            data = query_api('videos', api_params)
            list_videos(data, page, plugin_params)
    else:
        page = int(page)
        api_params['offset'] = page * 100
        data = query_api('videos', api_params)
        list_videos(data, page, plugin_params)

    xbmcplugin.endOfDirectory(addon_id)

@handler.handler
def endurance(gb_filter):
    runs = [ 'Chrono Trigger', 'Deadly Premonition', 'Persona 4',
             'The Matrix Online' ]

    for run in runs:
        url = handler.build_url({ 'mode': 'videos', 'page': 'all',
                                  'gb_filter': gb_filter + ',name:%s' % run })
        li = xbmcgui.ListItem(run, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_id, url=url,
                                    listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_id)

@handler.handler
def search(query=None, page='0'):
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
                                 'offset': page*100 })
    list_videos(data, page, { 'mode': 'search', 'query': query })
    xbmcplugin.endOfDirectory(addon_id)

@handler.handler
def play(url):
    li = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(addon_id, True, li)

if my_addon.getSetting('api_key'):
    API_KEY = my_addon.getSetting('api_key')

xbmcplugin.setContent(addon_id, 'movies')
xbmcplugin.setPluginFanart(addon_id, my_addon.getAddonInfo('fanart'))

handler.run(sys.argv[2])
