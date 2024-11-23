# Scrapy settings for realtor project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html


# import logging

# # Configure logging
# LOG_ENABLED = True
# LOG_ENCODING = 'utf-8'
# LOG_FILE = 'realtor/crawls/realtor_scraper_log.txt'  # Specify the log file name
# LOG_LEVEL = 'INFO'  # Log all levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
# LOG_STDOUT = True  # Redirect stdout and stderr to the log

# # Customize the logging format if needed (optional)
# LOG_FORMAT = '%(levelname)s: %(message)s'
# LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# LOG_LEVEL = 'INFO'
LOG_LEVEL = 'ERROR'


RETRY_TIMES = 3
# RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]
RETRY_HTTP_CODES = []
HEADERS_UPDATE_WAIT = 10

SAVE_POINTS_DIR = "realtor/crawl_jobs/temporary_save_points"
PRIMARY_OUTPUTS_DIR = "realtor/primary_outputs"
OUTPUT_DIR = "realtor/outputs"


BOT_NAME = "realtor"

INPUT_FILE = "realtor inputs.txt"

SCRAPING_HEADERS = {}

SPIDER_MODULES = ["realtor.spiders"]
NEWSPIDER_MODULE = "realtor.spiders"

RESULTS_PER_PAGE = 42

SCRAPING_HEADERS = {}

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "realtor (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False
# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 100


# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "realtor.middlewares.RealtorSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
   "realtor.middlewares.RealtorDownloaderMiddleware": 543,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    "realtor.pipelines.RealtorPipeline": 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

"""
I am working on a scrapy project where I want to use the downloader middleware to
manage the requests made by its spider, the requests need a specific set of headers 
in order to success "self.scraping_headers" which are attained from the "SCRAPING_HEADERS" variable in the settings
, I want the downloader middleware to generate the "self.scraping_headers" by running the "Get_Headers().fresh_headers()"
method if the "SCRAPING_HEADERS" variable is empty, also in case a request fails it stops
the the requests made after it until it update the "self.scraping_headers" then update these requests headers and try
again, and if the requests that were sent before capturing the failed request got an unsuccessful response 
and they have different headers from the "self.scraping_headers" I want their headers to be updated and resent, can you do that for me.
"""