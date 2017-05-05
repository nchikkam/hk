import unittest
import requests_mock

from lib.crawler import SiteMap

class SiteMapUnitTests(unittest.TestCase):

    def test_sitemap_instance_creation(self):
        """
            Verify that the creation of the sitemap works without arguments
        :return: None
        """
        site_map = SiteMap()
        self.assertEqual(site_map.site_map, {})
        self.assertEqual(site_map.unvisited, set([]))
        self.assertEqual(site_map.start_page, None)

    def test_compose_url_from_hash_href(self):
        """
            Verify composing big urls based on domain and intra links
        :return: None
        """
        href = "#intra-link"
        url = 'http://www.ywallet.com'
        actual = SiteMap().compose_url_from_href(url, href)
        expected = 'http://www.ywallet.com#intra-link'
        self.assertEqual(expected, actual)

    def test_compose_url_from_relative_link_href(self):
        """
            verifies that href relative links composition works fine.
        :return: None
        """
        href = "./intra-link"
        url = 'http://www.ywallet.com'
        actual = SiteMap().compose_url_from_href(url, href)
        expected = 'http://www.ywallet.com/intra-link'
        self.assertEqual(expected, actual)

    def test_compose_url_from_relative_startingwithslash_href(self):
        """
            verifies that href absolute composition works fine.
        :return: None
        """
        href = "/intra-link"
        url = 'http://www.ywallet.com'
        actual = SiteMap().compose_url_from_href(url, href)
        expected = 'http://www.ywallet.com/intra-link'
        self.assertEqual(expected, actual)

    def test_compose_url_from_with_properurl(self):
        """
            verifies that href composition works if the protocol scheme is missing in the input parameters.
        :return: None
        """
        href = "http://www.ywallet.com"
        url = None
        actual = SiteMap().compose_url_from_href(url, href)
        expected = 'http://www.ywallet.com'
        self.assertEqual(expected, actual)

    def test_get_out_going_links_works_fine(self):
        valid_links = [
            "http://nonexistingurl.com/about.html",
            "http://nonexistingurl.com/help.html",
            "./products.html",
            "/samples.html",
            "http://nonexistingurl.com/path?a=b#dummy"
        ]

        anchors = ""
        for link in valid_links:
            anchors += "<a href=\"{0}\">link</a>\n".format(link)

        html = "<html><body>{0}</body></html>".format(anchors)

        expected = [
            "http://nonexistingurl.com/about.html",
            "http://nonexistingurl.com/help.html",
            "http://nonexistingurl.com/products.html",
            "http://nonexistingurl.com/samples.html",
            "http://nonexistingurl.com/path",
        ]

        subject = SiteMap()
        subject.set_start_page("nonexistingurl.com")
        url = "http://nonexistingurl.com"
        actual = subject.get_out_going_links(url, html)
        for e in expected:
            self.assertTrue(e in actual)

    def test_get_out_going_invalid_links_filter_works_fine(self):
        valid_links = [
            "http://nonexistingurl.com/about.html",
            "http://nonexistingurl.com/help.html",
            "./products.html",
            "/samples.html",
            "http://nonexistingurl.com/path?a=b#dummy",
            "/stats.zip",
            "/records.gz",
        ]

        anchors = ""
        for link in valid_links:
            anchors += "<a href=\"{0}\">link</a>\n".format(link)

        html = "<html><body>{0}</body></html>".format(anchors)

        expected = [
            "http://nonexistingurl.com/about.html",
            "http://nonexistingurl.com/help.html",
            "http://nonexistingurl.com/products.html",
            "http://nonexistingurl.com/samples.html",
            "http://nonexistingurl.com/path",
        ]

        subject = SiteMap()
        subject.set_start_page("nonexistingurl.com")
        url = "http://nonexistingurl.com"
        actual = subject.get_out_going_links(url, html)
        for e in expected:
            self.assertTrue(e in actual)

    def test_site_map_creation_works_fine(self):
        """create dummy page with links, create sitemap and compare"""
        valid_links = ["http://nonexistingurl.com/about.html"]

        anchors = ""
        for link in valid_links:
            anchors += "<a href=\"{0}\">link</a>\n".format(link)

        html = "<html><body>{0}</body></html>".format(anchors)
        url = "http://nonexistingurl.com"
        subject = SiteMap()
        subject.set_start_page(url)

        headers = {'Date': "dummy date"}
        subject.get_assets(url, headers=headers, html_body=html)

        expected = {'http://nonexistingurl.com':
            {   'css': [],
                'date': 'dummy date',
                'img': [],
                'js': [],
                'links': valid_links
            }
        }

        for url in subject.site_map:
            for k in subject.site_map[url]:
                self.assertEquals(subject.site_map[url][k], expected[url][k])

    def test_site_map_creation_works_fine_excluding_links_in_comments(self):
        """create dummy page with links, create sitemap and compare"""
        valid_links = ["http://nonexistingurl.com/about.html"]

        anchors = ""
        for link in valid_links:
            anchors += "<a href=\"{0}\">link</a>\n".format(link)

        html = "<html><!-- <a href=\"https://ywallet.com\"/> --><body>{0}</body></html>".format(anchors)
        url = "http://nonexistingurl.com"
        subject = SiteMap()
        subject.set_start_page(url)

        headers = {'Date': "dummy date"}
        subject.get_assets(url, headers=headers, html_body=html)

        expected = {'http://nonexistingurl.com':
            {   'css': [],
                'date': 'dummy date',
                'img': [],
                'js': [],
                'links': valid_links
            }
        }

        for url in subject.site_map:
            for k in subject.site_map[url]:
                self.assertEquals(subject.site_map[url][k], expected[url][k])

    @requests_mock.mock()
    def test_access_page_works_fine(self, m):
        url = "http://www.dummy.com"
        m.get(url, text="200")

        subject = SiteMap()
        subject.set_start_page(url)
        resp = subject.access_page(url)
        self.assertEquals(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()