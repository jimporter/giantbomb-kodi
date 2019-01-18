import resources.lib.giantbomb as giantbomb
import time
import unittest


class TestGiantBombAPI(unittest.TestCase):
    def setUp(self):
        self.gb = giantbomb.GiantBomb()

    def test_categories(self):
        data = self.gb.query('video_types')

        self.assertIsInstance(data['number_of_total_results'], int)
        self.assertEquals(data['number_of_total_results'],
                          data['number_of_page_results'])
        self.assertEquals(data['number_of_page_results'], len(data['results']))

        for video_type in data['results']:
            self.assertIsInstance(video_type['name'], unicode)
            self.assertIsInstance(video_type['id'], int)

    def test_videos(self):
        data = self.gb.query('videos')

        self.assertEquals(data['number_of_page_results'], 100)
        self.assertEquals(data['number_of_page_results'], len(data['results']))

        for video in data['results']:
            self.assertIsInstance(video['name'], basestring)
            self.assertIsInstance(video['deck'], basestring)
            self.assertIsInstance(video['length_seconds'], int)

            self.assertIsInstance(video['publish_date'], unicode)
            time.strptime(video['publish_date'], '%Y-%m-%d %H:%M:%S')

            self.assertIsInstance(video['image']['super_url'], unicode)
            self.assertIsInstance(video['high_url'], unicode)

    def test_latest(self):
        default = self.gb.query('videos')
        desc = self.gb.query('videos', { 'sort': 'publish_date:desc' })

        for expectedvid, actualvid in zip(default['results'], desc['results']):
            for key, expected in expectedvid['image'].iteritems():
                actual = actualvid['image'][key]
                if actual[0] == '/':
                    actual = 'http://static.giantbomb.com' + actual
                if expected[0] == '/':
                    expected = 'http://static.giantbomb.com' + expected
                self.assertEquals(actual, expected)
