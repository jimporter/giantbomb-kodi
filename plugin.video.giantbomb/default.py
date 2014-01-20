from resources.lib.giantbomb import GiantBomb
from resources.lib.requesthandler import RequestHandler

import sys
import time
import urllib
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui

addon_id = int(sys.argv[1])
my_addon = xbmcaddon.Addon('plugin.video.giantbomb')

def update_api_key(api_key):
    my_addon.setSetting('api_key', api_key)

gb = GiantBomb(my_addon.getSetting('api_key') or None, update_api_key)
handler = RequestHandler(sys.argv[0])

xbmcplugin.setContent(addon_id, 'movies')
xbmcplugin.setPluginFanart(addon_id, my_addon.getAddonInfo('fanart'))

@handler.page
def link_account(first_run=False):
    """Link this XBMC profile to the user's Giant Bomb account by asking them to
    go to a link on their computer and get a link code.

    :param first_run: True if this is the first time the add-on has been run;
                      False otherwise"""

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
            if gb.get_api_key(link_code):
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

@handler.page
def unlink_account():
    """Unlink this XBMC profile from the user's Giant Bomb account."""

    dialog = xbmcgui.Dialog()
    ok = dialog.yesno('Oh no!',
                      'Are you sure you want to unlink your account?',
                      yeslabel='Unlink', nolabel='Cancel')
    if ok:
        my_addon.setSetting('api_key', '')

@handler.default_page
def categories():
    """Display the list of video categories from Giant Bomb."""

    if my_addon.getSetting('first_run') == 'true':
        if not my_addon.getSetting('api_key'):
            link_account(first_run=True)
        my_addon.setSetting('first_run', 'false')

    data = gb.query('video_types')
    # Count up the total number of categories; add one for "Latest" and one more
    # for "Search".
    total = data['number_of_total_results'] + 2

    # Add the "Latest" pseudo-category
    url = handler.build_url({ 'mode': 'videos' })
    li = xbmcgui.ListItem('Latest', iconImage='DefaultFolder.png')
    li.setProperty('fanart_image', my_addon.getAddonInfo('fanart'))
    xbmcplugin.addDirectoryItem(handle=addon_id, url=url,
                                listitem=li, isFolder=True,
                                totalItems=total)

    # Add all the real categories
    for category in data['results']:
        name = category['name']
        mode = 'endurance' if category['id'] == 5 else 'videos'
        url = handler.build_url({
                'mode': mode,
                'gb_filter': 'video_type:{0}'.format(category['id'])
                })
        li = xbmcgui.ListItem(category['name'], iconImage='DefaultFolder.png')
        li.setProperty('fanart_image', my_addon.getAddonInfo('fanart'))
        xbmcplugin.addDirectoryItem(handle=addon_id, url=url,
                                    listitem=li, isFolder=True,
                                    totalItems=total)

    # Add the "Search" pseudo-category
    url = handler.build_url({ 'mode': 'search' })
    li = xbmcgui.ListItem('Search', iconImage='DefaultFolder.png')
    li.setProperty('fanart_image', my_addon.getAddonInfo('fanart'))
    xbmcplugin.addDirectoryItem(handle=addon_id, url=url,
                                listitem=li, isFolder=True,
                                totalItems=total)

    xbmcplugin.endOfDirectory(addon_id)

def list_videos(data, page, plugin_params=None):
    """Given a JSON response from Giant Bomb with a bunch of videos, add them to
    XBMC.

    :param data: The JSON response
    :param page: The 0-offset page number, or 'all' to show all pages
    :param plugin_params: An optional dict of parameters to pass back to the
                          plugin; used for navigating between pages"""

    quality_mapping = ['low_url', 'high_url', 'hd_url']
    quality = quality_mapping[ int(my_addon.getSetting('video_quality')) ]

    page_menu = []

    # Make sure this value is an int, since Giant Bomb currently returns this as
    # a string.
    total = int(data['number_of_total_results'])
    if page == 'all':
        this_page = total
    else:
        this_page = len(data['results'])

        if page > 0:
            url = handler.build_url(dict(page=page-1, **plugin_params))
            page_menu.append(('Previous page',
                              'Container.Update({0}, replace)'.format(url)))
        if (page+1) * 100 < total:
            url = handler.build_url(dict(page=page+1, **plugin_params))
            page_menu.append(('Next page',
                              'Container.Update({0}, replace)'.format(url)))

    for video in data['results']:
        name = video['name']
        date = time.strptime(video['publish_date'], '%Y-%m-%d %H:%M:%S')
        duration = video['length_seconds']

        # Build the URL for playing the video
        remote_url = video.get(quality, video['high_url'])
        if quality == 'hd_url' and 'hd_url' in video:
            # XXX: This assumes the URL already has a query string!
            remote_url += '&' + urllib.urlencode({ 'api_key': gb.api_key })

        li = xbmcgui.ListItem(name, iconImage='DefaultVideo.png',
                              thumbnailImage=video['image']['super_url'])
        li.addStreamInfo('video', { 'duration': duration })
        li.setInfo('video', infoLabels={
                'title': name,
                'plot': video['deck'],
                'date': time.strftime('%d.%m.%Y', date),
                })
        li.setProperty('IsPlayable', 'true')

        if video.get('youtube_id'):
            youtube_item = (
                'Play with Youtube',
                ('PlayMedia(plugin://plugin.video.youtube/?action=play_video' +
                 '&videoid={0})').format(video['youtube_id']))
            li.addContextMenuItems([youtube_item] + page_menu)
        else:
            li.addContextMenuItems(page_menu)

        li.setProperty('fanart_image', my_addon.getAddonInfo('fanart'))
        xbmcplugin.addDirectoryItem(handle=addon_id, url=remote_url,
                                    listitem=li, totalItems=this_page)

@handler.page
def videos(gb_filter=None, page='0'):
    """List the videos satisfying some filter criteria.

    :param gb_filter: A filter to send to the Giant Bomb API to filter the video
                      results
    :param page: A 0-offset page number (as a string); or 'all' to show all
                 pages"""

    api_params = { 'sort': 'publish_date:desc' }
    plugin_params = { 'mode': 'videos' }

    if gb_filter:
        api_params['filter'] = plugin_params['gb_filter'] = gb_filter

    if page == 'all':
        data = gb.query('videos', api_params)
        list_videos(data, page, plugin_params)
        # Make sure this value is an int, since Giant Bomb currently returns
        # this as a string.
        total = int(data['number_of_total_results'])

        for offset in range(100, total, 100):
            api_params['offset'] = offset
            data = gb.query('videos', api_params)
            list_videos(data, page, plugin_params)
    else:
        page = int(page)
        api_params['offset'] = page * 100
        data = gb.query('videos', api_params)
        list_videos(data, page, plugin_params)

    xbmcplugin.endOfDirectory(addon_id)

@handler.page
def endurance(gb_filter):
    """Show the list of Endurance Runs.

    :param gb_filter: A filter to pass to the Giant Bomb API (this should be a
                      filter to show only videos with the Endurance Run
                      category)"""

    runs = [ 'Chrono Trigger', 'Deadly Premonition', 'Persona 4',
             'The Matrix Online' ]

    for run in runs:
        url = handler.build_url({
                'mode': 'videos', 'page': 'all',
                'gb_filter': '{0},name:{1}'.format(gb_filter, run) })
        li = xbmcgui.ListItem(run, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_id, url=url,
                                    listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_id)

@handler.page
def search(query=None, page='0'):
    """Show some search results from the Giant Bomb API, or prompt the user to
    enter a search query.

    :param query: The search query
    :param page: A 0-offset page number (as a string)"""

    page = int(page)

    if query is None:
        keyboard = xbmc.Keyboard('', 'Search', False)
        keyboard.doModal()
        if keyboard.isConfirmed():
            query = keyboard.getText()
        else:
            xbmc.executebuiltin('Action(ParentDir)')
            return

    data = gb.query('search', { 'resources': 'video', 'query': query,
                                 'offset': page*100 })
    list_videos(data, page, { 'mode': 'search', 'query': query })
    xbmcplugin.endOfDirectory(addon_id)

handler.run(sys.argv[2])
