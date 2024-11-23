# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

import scrapy
from time import time, sleep
from realtor.spiders.headers_extractor import Get_Headers

import json
import os
from typing import Literal

from fake_useragent import UserAgent as UA


class RealtorSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)





class RealtorDownloaderMiddleware:
  
    update_number = 0
    total_requests_made = 0
    pbar = None
    fake_ua = UA(os="macos", browsers="safari")
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.crawler.request_batch_delay = None
        self.settings = self.crawler.settings
        self.headers_update_wait = self.settings.get('HEADERS_UPDATE_WAIT', 120)
        self.request_retry_times = self.settings.get('RETRY_TIMES', 3)
        self.batch_size = self.settings.get("CONCURRENT_REQUESTS", 100)
        
        if "scraping_headers.json" in os.listdir("realtor/spiders"):
            with open("realtor/spiders/scraping_headers.json", "r") as f:
                self.scraping_headers = json.load(f)
        else:
            self.update_scraping_headers()


    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler)
        return middleware
    
    def update_scraping_headers(self):
        self.scraping_headers = Get_Headers().fresh_headers(wait_period=120)
        with open("spiders\scraping_headers.json", "w") as f:
            json.dump(self.scraping_headers,f, indent=4)
    
    def modify_request_headers(self, request):
        for key, value in self.scraping_headers.items():
            if key != "referer":
                request.headers[key]= value
        
        request.meta['update_number'] = self.update_number
        return request
    
    def process_request(self, request, spider):
        self.total_requests_made+=1
        if not self.crawler.request_batch_delay:
            self.crawler.request_batch_delay = time()  
        self.modify_request_headers(request)
        return None

    def process_response(self, request, response, spider):
    
        if response.status != 200:

            if request.meta.get('update_number',1) == self.update_number:
                   
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
        
        else: 
            return response
            
        
