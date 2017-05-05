import requests                                 # to handle http requests
from urllib.parse import (
    urlparse,                                   # url parsing
    urldefrag
)
import json, sys                                # json and report error in generic except:
import logging
from urllib.robotparser import RobotFileParser  # to respect the robot.txt standard

from bs4 import BeautifulSoup                   # nice parser for html to avoid regexes

from gevent import pool, monkey                 # asynchronous threading io modules
monkey.patch_all()
sys.setrecursionlimit(2000)

class SiteMap():
    """ This class composes of all the functionalities needed to generate site_map"""

    def __init__(self, main_page=None, robotrules=True, threadcount=1):
        """ctor that checks args and decides to enable single or multithreaded
           generation of sitemap
        """
        logging.info("Consider Robot.txt ? ==> "+str(robotrules))
        self.robotrules = robotrules
        self.site_map = {}

        self.unvisited = set([])
        self.start_page = None

        self.robot_txt_rules = None

        if main_page:
            self.unvisited.add(main_page)
            try:
                self.start_page = urlparse(main_page).netloc
            except:
                logging.error("Improper URL, Please provide a Valid Url:"+main_page)
                exit(0)

        if self.robotrules == "True":
            try:
                logging.info("robot.txt respected")
                self.robot_txt_rules = RobotFileParser()
                self.robot_txt_rules.set_url(main_page + "/robots.txt")
                self.robot_txt_rules.read()
            except:
                logging.error("Unable to read the robot.txt file")
                self.robotrules = False # error reading robot.txt, ignore it forever

        self.threadcount = int(threadcount)

    def execute(self):
        if self.threadcount <= 1: # if single threaded model is chosen, avoid threading
            self.generate()
        else:
            self.start()          # fasten by multi threads

    def start(self):
        """This creates a pool of chosen limit so as to have the control and
           spawns the main function and waits until process and subsequently
           spawned process finish.
        """
        self.pool = pool.Pool(self.threadcount)
        self.pool.spawn(self.generate_parallels)
        self.pool.join()

        self.generate_reports()


    def generate(self):
        """Non multithreaded model method that crawls until all pages are
           crawled and assets are extracted. Once its done, it creates the
           sitemap and assets json file for the given domain.
        """
        while self.unvisited:
            self.crawl()

        self.generate_reports()

    def generate_reports(self):
        """composes the xml tags with the keys in site_map member which are
           nothing but the sitemap urls
        """
        header = """<?xml version="1.0" encoding="UTF-8"?>
                            <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
                            xmlns:xhtml="http://www.w3.org/1999/xhtml"
                            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                            xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
                            http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
                        """
        footer = """\n</urlset>\n"""
        entry = "\t<url><loc>%s</loc></url>\n"

        xml = header
        for url in self.site_map.keys():
            xml += entry % (url)

        xml += footer
        name = self.start_page.replace(".", "_")
        self.create_file("%s.xml" % (name), xml)
        self.create_file("%s_assets.json" % (name), json.dumps(self.site_map, indent=2, sort_keys=True))


    def generate_parallels(self):
        """
            This method is similar to recursive in a way that crawls pages and clears
            the queue, which is self.unvisited. It stops when there are no urls to crawl
            and all threads in pool are empty i.e they are not active anymore due to
            finishing of crawling. Since its spawning a new thread and not calling
            directly, it is a nice way to go about it for now :)
            [Note:] There is a limit for recursion in Python and it can be increased by
            sys.setrecursionlimit(1500)

            An assumption has been made for this implementation that a website that has
            more than 500 nested links needs a bit higher design in terms to store the
            assets which might go above a hundred MB. In such cases, this can just be
            converted into a loop. More over, there is no extra stack variables.
        """
        self.crawl()
        while len(self.unvisited) > 0 and not self.pool.full():
            self.pool.spawn(self.generate_parallels)

    def create_file(self, file, content):
        """writes the given content to the file"""
        f = open(file, 'w')
        f.write(content)
        f.close()

    def compose_url_from_href(self, page, href):
        """composes a proper url from domainlink and intralinks with in the page"""
        url = urlparse(page)

        if href.startswith('/'):
            return "http://%s%s"%(url.netloc, href)
        elif href.startswith('#'):
            return "http://%s%s%s"%(url.netloc, url.path, href)
        elif href.startswith('./'):
            return "http://%s%s"%(url.netloc, href[1:])
        elif not href.startswith('http'):
            return "http://" + url.netloc + '/' + href
        elif href.endswith('/'):
            return href[:-1]

        return href

    def get_out_going_links(self, page, html_body):
        """extracts all the outgoing links and adds links that belong to
           main page domain for further crawling if they are not crawled yet
           This avoids:
            - links that are .zip files
            - links mentioned in href that are javascript methods
            - mailto: links

        """
        soup = BeautifulSoup(html_body, "html.parser")
        valid_links_for_this_page = []
        for a in soup.find_all('a', href=True):

            href = a['href'].lower()
            href = self.compose_url_from_href(page, href)

            # clean the href so that it will have legitimate urls instead of #cluttered ones and q=param prints
            href = urldefrag(href)[0]  # skip intra links [this took time to find out !] ##1
            # remove query params as only the path matters
            if href.find('?') != -1:
                href = href[:href.find('?')]  ##2

            new_page = urlparse(href)

            # add to the queue only it it doesn't cause a cycle
            # assumption: if a link ends with domain.com, assuming it can be crawled to make sitemap complete
            if  not str(new_page.netloc).endswith(self.start_page):          # doesn't belong to domain
                valid_links_for_this_page.append(href)
                continue

            if  self.robot_allows(href) and \
                not href in self.site_map            and \
                not href in self.unvisited                  and \
                not 'javascript:' in href           and \
                not 'mailto:' in href:
                if not ( href.endswith(".zip") or
                             href.endswith(".gz") or
                             href.endswith(".gzip") or
                             href.endswith(".tar") or
                             href.endswith(".bz2") or
                             href.endswith(".jpg") or
                             href.endswith(".png") or
                             href.endswith(".exe")
                         ):
                    self.unvisited.add(href)
                valid_links_for_this_page.append(href)

        return valid_links_for_this_page

    def get_assets(self, page, headers, html_body):
        """A nice feature of response header is that it reports the last-modified
           time of the link on the server. If we are doing regular crawling, we can
           avoid if the link is not updates since the last time. This method is
           useful for indexing the data so as to minimize the crawling effort to
           save execution time.
           It updates the site_map dictionary with the links, css, images and scripts
        """
        if 'last-modified' in headers:
            date = headers['Last-Modified']
        else:
            date = headers['Date']

        soup = BeautifulSoup(html_body, "html.parser")
        img = soup.findAll("img")
        css = soup.findAll("link", {"rel": "stylesheet"})
        js = soup.findAll('script')

        self.site_map[page] = {
            'date': date,
            'links': self.get_out_going_links(page, html_body),
            'css': [c['href'] for c in css],
            'img': [i['src'] for i in img],
            'js': [x.get('src', 'inline jscode') for x in js]
        }


    def crawl(self):
        """This actually opens the url and calls the assets method """
        if len(self.unvisited) <= 0:
            return
        page = self.unvisited.pop()
        if page in self.site_map:
            return
        logging.info("Starting to Crawl Page: " + page)

        try:
            response = self.access_page(page)
            if (response.status_code != 200):
                return None

            html_body = response.text

            self.get_assets(page, response.headers, html_body)
        except:
            logging.error("Issue while opening url: %s" + page)
            return None
        logging.debug("Crawled Pages: {}".format(len(self.site_map)))

    def access_page(self, url):
        """accesses the url from the server. This method was created
            to enable mock tests.
        """
        return requests.get(url)

    def get_site_map(self):
        """exposes site_map"""
        return self.site_map

    def set_start_page(self, url):
        """sets the start page for the crawler"""
        self.start_page = url

    def robot_allows(self, link):
        """method to check if link can be accessed as per robot rules"""
        if not self.robotrules: return True
        try:
            if self.robot_txt_rules.can_fetch("*", link):
                    return True
            return False
        except:
            return True