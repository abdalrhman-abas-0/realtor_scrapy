"""
This module defines the middleware for the Scrapy project, specifically designed for realtor.com scraping.
It includes custom spider and downloader middleware to handle requests, responses, and exceptions efficiently.

Classes:
    RealtorSpiderMiddleware: Middleware for managing spider-level processing of requests and responses.
    RealtorDownloaderMiddleware: Middleware for managing downloader-level processing, including dynamic header updates
                                 and retry mechanisms for failed requests.
"""

from scrapy import signals
import scrapy
from time import time, sleep
from realtor.spiders.headers_extractor import Get_Headers
import json
import os
from typing import Literal
from fake_useragent import UserAgent as UA


class RealtorSpiderMiddleware:
    """
    Spider middleware for managing the flow of requests and responses at the spider level.
    Allows for handling exceptions, modifying results, and initializing spider-specific operations.
    """

    @classmethod
    def from_crawler(cls, crawler):
        """
        Factory method to create an instance of the middleware and connect it to Scrapy signals.

        Args:
            crawler (scrapy.crawler.Crawler): The Scrapy crawler instance.

        Returns:
            RealtorSpiderMiddleware: An instance of the middleware.
        """
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        """
        Processes responses before they reach the spider.

        Args:
            response (scrapy.http.Response): The HTTP response object.
            spider (scrapy.Spider): The Scrapy spider instance.

        Returns:
            None: If no exception is raised, the response proceeds to the spider.
        """
        return None

    def process_spider_output(self, response, result, spider):
        """
        Processes the results returned by the spider.

        Args:
            response (scrapy.http.Response): The HTTP response object.
            result (iterable): The results (items or requests) returned by the spider.
            spider (scrapy.Spider): The Scrapy spider instance.

        Returns:
            iterable: The processed results.
        """
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        """
        Handles exceptions raised during spider processing.

        Args:
            response (scrapy.http.Response): The HTTP response object.
            exception (Exception): The exception raised.
            spider (scrapy.Spider): The Scrapy spider instance.

        Returns:
            None: Allows other middleware to handle the exception.
        """
        pass

    def process_start_requests(self, start_requests, spider):
        """
        Processes the initial requests before they are sent to the downloader.

        Args:
            start_requests (iterable): The initial requests of the spider.
            spider (scrapy.Spider): The Scrapy spider instance.

        Returns:
            iterable: The processed requests.
        """
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        """
        Logs a message when the spider is opened.

        Args:
            spider (scrapy.Spider): The Scrapy spider instance.
        """
        spider.logger.info("Spider opened: %s" % spider.name)


class RealtorDownloaderMiddleware:
    """
    Downloader middleware for managing request headers, handling retries, and updating scraping headers dynamically.

    Attributes:
        update_number (int): Tracks the number of header updates.
        total_requests_made (int): Tracks the total number of requests processed.
        pbar (Optional[Any]): Placeholder for a progress bar or tracking utility.
        fake_ua (fake_useragent.UserAgent): Fake user-agent generator for dynamic user-agent strings.
    """
    update_number = 0
    total_requests_made = 0
    pbar = None
    fake_ua = UA(os="macos", browsers="safari")

    def __init__(self, crawler):
        """
        Initializes the middleware with crawler settings and header management utilities.

        Args:
            crawler (scrapy.crawler.Crawler): The Scrapy crawler instance.
        """
        self.crawler = crawler
        self.crawler.request_batch_delay = None
        self.settings = self.crawler.settings
        self.headers_update_wait = self.settings.get('HEADERS_UPDATE_WAIT', 120)
        self.request_retry_times = self.settings.get('RETRY_TIMES', 3)
        self.batch_size = self.settings.get("CONCURRENT_REQUESTS", 100)

        # Load or generate scraping headers
        if "scraping_headers.json" in os.listdir("realtor/spiders"):
            with open("realtor/spiders/scraping_headers.json", "r") as f:
                self.scraping_headers = json.load(f)
        else:
            self.update_scraping_headers()

    @classmethod
    def from_crawler(cls, crawler):
        """
        Factory method to create an instance of the middleware.

        Args:
            crawler (scrapy.crawler.Crawler): The Scrapy crawler instance.

        Returns:
            RealtorDownloaderMiddleware: An instance of the middleware.
        """
        middleware = cls(crawler)
        return middleware

    def update_scraping_headers(self):
        """
        Updates the scraping headers by generating fresh headers and saving them to a JSON file.
        """
        self.scraping_headers = Get_Headers().fresh_headers(wait_period=120)
        with open("spiders/scraping_headers.json", "w") as f:
            json.dump(self.scraping_headers, f, indent=4)

    def modify_request_headers(self, request):
        """
        Modifies request headers with dynamic scraping headers.

        Args:
            request (scrapy.http.Request): The HTTP request object.

        Returns:
            scrapy.http.Request: The modified request.
        """
        for key, value in self.scraping_headers.items():
            if key != "referer":
                request.headers[key] = value

        request.meta['update_number'] = self.update_number
        return request

    def process_request(self, request, spider):
        """
        Processes each request before it is sent to the server.

        Args:
            request (scrapy.http.Request): The HTTP request object.
            spider (scrapy.Spider): The Scrapy spider instance.

        Returns:
            None: If no modifications are needed.
        """
        self.total_requests_made += 1
        if not self.crawler.request_batch_delay:
            self.crawler.request_batch_delay = time()
        self.modify_request_headers(request)
        return None

    def process_response(self, request, response, spider):
        """
        Processes each response, handling retries and updating headers if necessary.

        Args:
            request (scrapy.http.Request): The original request.
            response (scrapy.http.Response): The HTTP response object.
            spider (scrapy.Spider): The Scrapy spider instance.

        Returns:
            scrapy.http.Request or scrapy.http.Response: The processed response or a retry request.
        """
        if response.status != 200:
            if request.meta.get('update_number', 1) == self.update_number:
                self.crawler.engine.pause()
                if response.status == 502 and request.meta.get('retry_count', 0) <= 0:
                    sleep(5)
                else:
                    self.update_scraping_headers()
                    sleep(self.headers_update_wait)
                    sleep(61)
                    self.crawler.request_batch_delay = time()
                self.crawler.engine.unpause()

            request = self.modify_request_headers(request)
            retry_count = request.meta.get('retry_count', 0) + 1
            if retry_count <= self.request_retry_times:
                request.meta['retry_count'] = retry_count
            return request

        return response
