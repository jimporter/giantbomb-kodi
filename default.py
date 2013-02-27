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
    return sys.argv[0] + "?" + urllib.urlencode(query)

def list_categories():
    data = query_api('video_types')
    total = data['number_of_total_results']
    for category in data['results']:
        name = category['name']
        url = build_url({ 'mode': 'video_type', 'id': category['id'] })
        li = xbmcgui.ListItem(name, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_id, url=url,
                                    listitem=li, isFolder=True,
                                    totalItems=total)
    xbmcplugin.endOfDirectory(addon_id)

def list_videos(video_type):
    xbmcplugin.addSortMethod(addon_id, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(addon_id, xbmcplugin.SORT_METHOD_TITLE)

    offset = 0
    while True:
        data = query_api('videos', { 'video_type': video_type,
                                     'offset': offset })
        total = data['number_of_total_results']
        offset += data['limit']
        for video in data['results']:
            name = video['name']
            remote_url = video['high_url']
            url = build_url({'mode': 'play', 'url': remote_url})
            date = time.strptime(video['publish_date'], '%Y-%m-%d %H:%M:%S')

            li = xbmcgui.ListItem(name, iconImage='DefaultVideo.png')
            if not first_li:
                first_li = li
                thumb = video['image']['super_url']
            li.setInfo(type='Video', infoLabels={
                    'Title': name,
                    'Plot': video['deck'],
                    'Date': time.strftime('%d.%m.%Y', date),
                    })
            li.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(handle=addon_id, url=url,
                                        listitem=li, totalItems=total)
        if offset >= total:
            break
    xbmcplugin.endOfDirectory(addon_id)


def play_video(url):
    li = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(addon_id, True, li)

params = urlparse.parse_qs(re.sub(r'^\?', '', sys.argv[2]))
mode = params.get('mode', [None])[0]

if mode is None:
    list_categories()
elif mode == 'video_type':
    list_videos(params['id'][0])
elif mode == 'play':
    play_video(params['url'][0])


