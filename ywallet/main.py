import argparse
import logging

from lib.crawler import SiteMap
from lib.util import timeit

logging.basicConfig(
    level=logging.FATAL,
    format='%(asctime)s %(filename)s: %(levelname)s: '
           '%(funcName)s(): %(lineno)d: %(message)s')

logger = logging.getLogger(__name__)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Sitemap and Assets generator for a give URL')

    parser.add_argument('--rooturl', help='the main webpage to start the sitemap generation')
    parser.add_argument('--robotrules', help='ignore the robot.txt rules if it\'s there')
    parser.add_argument('--threadcount', help='parallel threads to crawl to fasten the process')

    args = parser.parse_args()

    @timeit
    def generate_site_map(url, robot, count):
        s = SiteMap(args.rooturl, args.robotrules, args.threadcount)
        s.execute()

if  args.rooturl and args.robotrules and args.threadcount:
    generate_site_map(args.rooturl, args.robotrules, args.threadcount)
else:
    logging.info("Please pass all the positional Arguments")
    logging.info("run 'main.py - -help' for additional details on launching the process")