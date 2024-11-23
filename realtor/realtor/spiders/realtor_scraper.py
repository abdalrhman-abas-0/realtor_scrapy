import scrapy
from scrapy.http import JsonRequest
from scrapy import signals
from scrapy.exceptions import DontCloseSpider

from realtor.items import Listings_Object_For_Sale, RealtorItemLoader
from realtor.constants import PRIMARY_REQUEST_DATA,SECONDARY_PAYLOAD, STATES, STATES_CODES


from datetime import datetime,date, timedelta 
from typing import Literal
from time import time
import jmespath
import os


# scrapy crawl realtor_scraper -a scrape_all=False 

class RealtorScraperSpider(scrapy.Spider):
    name = "realtor_scraper"
    allowed_domains = ["www.realtor.com"]
    start_urls = ["https://www.realtor.com"]
    allowed_domains = ["www.realtor.com"]
    WEBSITE ="https://www.realtor.com"
    Primary_API = WEBSITE + "/api/v1/rdc_search_srp?client_id=rdc-search-for-sale-search&schema=vesta"
    RESULTS_PER_PAGE = 42
    page_requests_sent = 0
    page_requests_received = 0
    Secondary_API = WEBSITE+"/api/v1/hulk?client_id=detail-pages&schema=vesta"
    listings_requests_sent = 0
    listings_requests_received = 0
    headers_status = False
    pages_available:int
    results_available:int

    custom_settings = {
        "ITEM_PIPELINES": {
            'realtor.pipelines.Realtor_Pipeline': 300,
            },
        "JOBDIR": "realtor/crawl_jobs/realtor_spider_job",
        "CONCURRENT_REQUESTS": 10,
        "OUTPUT_DIR": "realtor/outputs"
    }

    
    # TODO convert the __init__ arguments to Literal
    def __init__(self, crawler, scrape_all, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.crawler = crawler
        self.settings = self.crawler.settings
        self.crawler.request_batch_delay = time()
        self.batch_size = self.settings.get('CONCURRENT_REQUESTS', 100)
        self.input_file = self.settings.get('INPUT_FILE', "realtor inputs.txt")
        self.scrape_all = True if scrape_all.lower() == "y" else False
        
        self.today = date.today()
        self.yesterday = self.today - timedelta(days = 1)


    @classmethod
    def from_crawler(cls, crawler, scrape_all, *args, **kwargs):
        spider = cls(crawler, scrape_all, *args, **kwargs) 
        crawler.signals.connect(spider.get_next_state, signal=signals.spider_idle)  
        return spider
           
    def get_next_state(self):
        self.__delete_the_scraped_state()
        with open(self.input_file, "r") as f:
            contents = f.read()
        if contents:
            self.crawler.engine.crawl(self.gen_requests())
            raise DontCloseSpider 
        else:
            return
    
    
    def get_initial_variables(self):
        if self.scrape_all or self.input_file not in os.listdir(): 
            self.__write_states_to_the_input_file(STATES)
            print(f"\nscraping all  the states")
        self.__get_state_name__code__listing_type()
    
        
    def start_requests(self):
        self.state["today"] = self.today   
        self.state["yesterday"] = self.yesterday
        yield self.gen_requests()
    
    def gen_requests(self):
        self.get_initial_variables()
        print(f'{'='*50}')
        print(f"\nscraping new listings for sale in {self.state["state_name"]} state.")
        self.page_requests_sent +=1
        headers, payload = self.__configure_primary_requests(1)
        return scrapy.Request(url=self.Primary_API, headers=headers, body=payload, method="POST", callback=self.run_primary_requests)

    
    def load_primary_requests_list(self,pages_available):
        return [
            {"headers": headers, "payload": payload} 
            for page_number in range(2, pages_available + 1) 
            for headers, payload in [self.__configure_primary_requests(page_number)]
        ]

            
    def run_primary_requests(self, response): 
        
        self.__get_pages_available(response)
        
        yield from self.run_secondary_requests(response)
        
        print(f"\n\nprimary_stage found {self.state["results_available"]} new for sale properties in {self.state["pages_available"]} pages. ") 
        self.crawler.total_requests_count = (self.state["pages_available"] + self.state["results_available"]) - self.page_requests_sent
        print(f"total requests to make: {self.crawler.total_requests_count}")
        
        for request in self.load_primary_requests_list(self.state["pages_available"]):
            self.page_requests_sent +=1
            yield scrapy.Request(url=self.Primary_API, headers=request["headers"], body=request["payload"], method="POST", callback=self.run_secondary_requests)  
 
        
    def run_secondary_requests(self, response):
        j_listings_prime_data = jmespath.search("data.home_search.properties",response.json())    
        self.page_requests_received +=1
        for listing in j_listings_prime_data:
            self.listings_requests_sent +=1
            headers, payload = self.__configure_secondary_requests(listing)
            yield scrapy.Request(url=self.Secondary_API, headers=headers, body=payload, method="POST", callback=self.parse)
           

    def parse(self,response):
        listing_data_item = RealtorItemLoader(Listings_Object_For_Sale(), selector= response)
        listing_data_item.add_jmes("state","data.home.location.address.state")
        listing_data_item.add_jmes("price","data.home.list_price")
        listing_data_item.add_jmes("URL","data.home.href")
        listing_data_item.add_jmes("property_id","data.home.property_id")
        listing_data_item.add_jmes("listing_id","data.home.listing_id")
        listing_data_item.add_jmes("type","data.home.description.type")
        listing_data_item.add_jmes("year_built","data.home.description.year_built")
        listing_data_item.add_jmes("street","data.home.location.address.line")
        listing_data_item.add_jmes("city","data.home.location.address.city")
        listing_data_item.add_jmes("state_code","data.home.location.address.state_code")
        listing_data_item.add_jmes("zip_code","data.home.location.address.postal_code")
        listing_data_item.add_jmes("bedrooms","data.home.description.beds")
        listing_data_item.add_jmes("bathrooms","data.home.description.baths")
        listing_data_item.add_jmes("sqft","data.home.description.sqft")
        listing_data_item.add_jmes("parameter","data.home.description.lot_sqft")
        listing_data_item.add_jmes("agent","data.home.advertisers[0].name")
        listing_data_item.add_jmes("office","data.home.advertisers[0].office.name")
        listing_data_item.add_jmes("agent_email","data.home.advertisers[0].email")
        listing_data_item.add_jmes("office_email","data.home.advertisers[0].office.email")
        listing_data_item.add_jmes("sold_date","data.home.last_sold_date")
        listing_data_item.add_jmes("status","data.home.status")
        listing_data_item.add_jmes("status","data.home.source.raw.status")

        self.listings_requests_received +=1
        yield listing_data_item.load_item()

 
    def __get_pages_available(self, response):
        results_available = response.json()["data"]["home_search"]["total"]
        
        if results_available%self.RESULTS_PER_PAGE == 0:
            pages_available = int(results_available/self.RESULTS_PER_PAGE)
        else:
            pages_available = int((results_available/self.RESULTS_PER_PAGE)+1)
        self.state["results_available"] = results_available
        self.state["pages_available"] = pages_available
        
           
    def __configure_primary_requests(self, page_number):
        headers = {}
        primary_request_data = PRIMARY_REQUEST_DATA.copy() 
        payload =primary_request_data["payload"].replace("**",self.state["state_name"]).replace("--", self.state_code)\
            .replace("==", str(self.state["yesterday"])).replace("++",str((page_number-1)*self.RESULTS_PER_PAGE))
        headers["referer"] = primary_request_data["referer"].replace("....", self.state["state_name"]).replace("*",str(page_number))
        return headers, payload
    
    
    def __configure_secondary_requests(self, request_data):
        headers = {}
        headers["referer"] = f"{self.WEBSITE}/realestateandhomes-detail/{request_data["permalink"]}"
        payload = SECONDARY_PAYLOAD.replace("**", str(request_data["property_id"])).replace("++", str(request_data["listing_id"]))
        return headers, payload
    
    def __write_states_to_the_input_file(self, states):
        with open(self.input_file,"w") as f:
            for state_name in states:
                f.write(f"{state_name}\n")
            
    def __get_state_name__code__listing_type(self):
        with open(self.input_file, "r") as f:
            contents = f.read()
        if contents:
            states_names_and_codes = dict(zip(STATES, STATES_CODES))
            self.state["state_name"] = contents.split("\n")[0].strip().replace(" ","-").lower()
            self.state_code = states_names_and_codes[self.state["state_name"]]
        else:
            raise ValueError('the input file "realtor inputs.txt" is empty!')    
        
    
    def __delete_the_scraped_state(self):
        with open(self.input_file,"r") as f:
            all_states = [state_name.strip().replace(" ","-").lower() for state_name in f.read().strip().split("\n")]
        if all_states[0].strip() == self.state["state_name"].strip():
            all_states.remove(self.state["state_name"])
            self.__write_states_to_the_input_file(all_states)
        else:
            print(f'\nall_states: {all_states}\nself.state["state_name"]: {self.state["state_name"]}\n')
            raise ValueError(f'the first state in the "{self.input_file}" does not match the scraped state {self.state["state_name"]}!') 
        