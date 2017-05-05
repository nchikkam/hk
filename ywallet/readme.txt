1. Project Title: Site Map and Assets for Each Link Generator.
----------------------------------------------------------------------------------
Description: 
	This is a small project that generates sitemap urls for a given domain along
	with the assets namely {hrefs, links, images, script} for each link. This 
	has a main class SiteMap that encapsulates the crawling functionality in a 
	tunable way according to user choices of enabling flag to respect robot.txt
	standard rules, flexibility to choose a thread count limit to spawn the crawl
	process so as to generate the sitemap urls and assets.

	The design takes into consideration of respecting the last-modified field of
	response header, threading model to speedup the crawling process. There are
	few tests that check the basic functionality of the crawler and results of 
	two manual tests that are manually tested against below sites in a voluntary
	way:
		json.org
		ywallet.com

	The run of this project generates the needed artifacts in the same folder where
	its launched.

Requirements:
----------------------------------------------------------------------------------
Packages and Notes:
	+ The code is written keeping python3 version in mind.
	+ In order to run this project, below packages must be installed:
	  Its assumed that pip3 is installed globally.
		pip install bs4 [BeautifulSoup]
		pip3 install requests-mock [mocking for requests module]
		pip3 install gevent [concurrency library to achieve parellalism]

2. Project Directory Structure:
----------------------------------------------------------------------------------
ywallet
│
├── crawlertests.py                              [unit tests for the crawler code]
│
├── lib
│   │
│   ├── __init__.py                    [file for python to tread folder as module]
│   │
│   ├── crawler.py               [main file that has all sitemap creation methods]
│   │
│   └── util.py                   [helper file to keep common methods, eg: timeit]
│
├── debugging
│   │
│   ├── json_org.xml                                [sitemap for json.org website]
│   ├── json_org_assets.json                         [assets for json.org website]
│   │
│   ├── json_org_29_threads_stats.log         [29 threads trace , took 10 seconds]
│   │
│   ├── json_org_single_process_stats.log        [single process, took 35 seconds]
│   │
│   ├── www_ywallet_com.xml                        [site map for ywallet.com site]
│   ├── www_ywallet_com_assets.json                  [assets for ywallet.com site]
│   │
│   ├── ywallet_10_threads_stats.log         [10 threads trace, took 2.55 seconds]
│   └── ywallet_single_process_stats.log       [single process, took 6.98 seconds]
│
│
├── main.py        [main code that validates arguments and reports the time taken]
│   
└── readme.txt                                                         [this file]

3. Steps to run the launcher:
----------------------------------------------------------------------------------
python3 main.py --rooturl <website> --robotrules <True|False> --threadcount <INTEGER>

4. Artifacts that the project produces:
----------------------------------------------------------------------------------
│
├── domain_name.xml         (sitemap file for the given domain)
│   
└── domain_name.json        (assets json file for the given domain)

Additional Notes: 
----------------------------------------------------------------------------------
.xml file will contain only the loc tags.
.json file will expose the assets such as href, .css, .img and .js files for each 
 of the url.

Challenges: 
----------------------------------------------------------------------------------
+ Depth to consider while crawling. The dfs approach might lead to infinite recursion, 
  so a BFS approach was chosen, which always makes sure that the stack overflow error
  will not occur.

+ A thought of attempting a set of retries, incase if the url responses are not being 
  served properly by the servie. This could be an extension.



Sample Runs Used During Development and Testing:
----------------------------------------------------------------------------------
python3 main.py --rooturl http://www.ywallet.com --robotrules True --threadcount 1
python3 main.py --rooturl http://www.ywallet.com --robotrules True --threadcount 10
python3 main.py --rooturl http://json.org --robotrules True --threadcount 1
python3 main.py --rooturl http://json.org --robotrules True --threadcount 29
