import sqlite3
import xbmc

class VideoDB(object):
    """A wrapper to the XBMC video database. Technically, we're not supposed to
    do this, but XBMC won't give us the info any other way."""

    def __init__(self, path=None):
        """Create a new instance of the video DB wrapper and get a cursor for
        the database.

        :param path: The path to the video database
        """

        if path is None:
            if xbmc.__version__ == '2.0':
                path = 'special://profile/Database/MyVideos75.db'
            elif xbmc.__version__ == '2.14.0':
                path = 'special://profile/Database/MyVideos78.db'
            else:
                raise Exception('Unknown XBMC Python version: ' +
                                xbmc.__version__)

        realpath = xbmc.translatePath(path)
        self._conn = sqlite3.connect(realpath)
        self._cursor = self._conn.cursor()

    def get_file_id(self, filename):
        """Get the file id for a file.

        :param filename: The filename
        :return: The file id or None if there's no such file
        """

        (basepath, leaf) = filename.rsplit('/', 1)
        basepath += '/'

        try:
            self._cursor.execute(
                'select idPath from path where strPath=?',
                (basepath,))
            pathid = self._cursor.fetchone()[0]

            self._cursor.execute(
                'select idFile from files where strFileName=? and idPath=?',
                (leaf, pathid))
            return self._cursor.fetchone()[0]
        except:
            return None

    def get_playback_info(self, fileid):
        """Get playback info for a file.

        :param fileid: The file id, retrieved from get_file_id
        :return: A dict with the playback info, or None if an error occurred
        """

        if fileid is None: return None

        try:
            self._cursor.execute(
                'select playCount, lastPlayed from files where idFile=?',
                (fileid,))
            info = self._cursor.fetchone()

            return { 'playcount': info[0], 'lastplayed': info[1] }
        except:
            return None

    def get_bookmark(self, fileid):
        """Get the bookmark for a file.

        :param fileid: The file id, retrieved from get_file_id
        :return: A dict with the bookmark info, or None if an error occurred
        """

        if fileid is None: return None

        try:
            self._cursor.execute(
                'select timeInSeconds, totalTimeInSeconds from bookmark ' +
                'where idFile=?',
                (fileid,))
            bookmark = self._cursor.fetchone()

            return { 'resumetime': bookmark[0], 'totaltime': bookmark[1] }
        except:
            return None

    def get_stream_details(self, fileid):
        """Get the stream details for a file.

        :param fileid: The file id, retrieved from get_file_id
        :return: A dict with the stream details, or None if an error occurred
        """

        if fileid is None: return None

        try:
            self._cursor.execute(
                'select strVideoCodec, fVideoAspect, iVideoWidth, ' +
                'iVideoHeight, iVideoDuration from streamdetails ' +
                'where idFile=? and iStreamType=0',
                (fileid,))
            video = self._cursor.fetchone()
        except:
            video = None

        try:
            self._cursor.execute(
                'select strAudioCodec, iAudioChannels, strAudioLanguage ' +
                'from streamdetails where idFile=? and iStreamType=1',
                (fileid,))
            audio = self._cursor.fetchone()
        except:
            audio = None

        if audio is None and video is None:
            return None

        result = {}
        if video:
            result['video'] = { 'codec': video[0], 'aspect': video[1],
                                'width': video[2], 'height': video[3],
                                'duration': video[4] }
        if audio:
            result['audio'] = { 'codec': audio[0], 'channels': audio[1],
                                'language': audio[2] }

        return result
