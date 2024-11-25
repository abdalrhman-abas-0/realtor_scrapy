import scrapy
from scrapy import signals
from scrapy.exceptions import DontCloseSpider

from realtor.items import Listing_Item, RealtorItemLoader
from realtor.constants import PRIMARY_REQUEST_DATA,SECONDARY_PAYLOAD, STATES, STATES_CODES


from datetime import date, timedelta 
from typing import Literal
from time import time
import jmespath
import os

class RealtorScraperSpider(scrapy.Spider):
    """
    scrapes Realtor for th for sale and sold listings.
    
    it scrapes the recently sold properties, the properties listed for 
    sale recently (within the last 24 hours) and all the properties
    listed for sale (within the last 15 days).
    
    it takes the states to look for listings in through a txt file 
    "realtor inputs.txt", scrapes the data and save then temporarily
    in a jsonl file in "crawl_jobs\\temporary_save_points" and after
    the scraping is completed it wipes the txt input file, deletes
    the jsonl file and save the final output as xlsx files in the 
    "outputs" directory.
    
    it can be paused and resumed seamlessly.
    
    Args:
        scrape_all (Literal["True","False"]): converted to bool with eval, whether to crawl 
            through all the USA states or stick to the states manually provided in the txt input file.
        listing_type (Literal["new_listings", "all_for_sale", "sold_listings"]): the type of listings 
            to scrape.

    Attributes:
    
        name (str): the name of the spider.
        allowed_domains (str): the domains allowed for crawling.
        WEBSITE (str): the main website to be scraped "Realtor".
        Primary_API (str): the URL of the API that have the results data of a search.
        Secondary_API (str): the URL of the API that have each listing data individually.
        RESULTS_PER_PAGE (int): the number of results appear for a search in the results page.
        page_requests_sent (int): tracks the number of requests sent to the search results API. 
        page_requests_received (int): tracks the number of requests received from the search results API.
        listings_requests_sent (int): tracks the number of requests sent to the listings API.
        listings_requests_received (int): tracks the number of requests received from the listings API 
        pages_available (int): the number of pages available for a search.
        results_available (int): the number of results available for a search.
        crawler (scrapy.crawler.Crawler): set by the "from_crawler" classmethod 
            after initiating the spider.
        settings (scrapy.settings.Settings): contains all the settings initiated in 
            the spider and the ones saved in the settings.py module.
        batch_size (int): the max number of concurrent requests.
        input_file (str): the the name and directory of the txt input file.
        today (datetime.date): the date of initiating a scraping session. 
        yesterday (datetime.date): the day before the scraping session 
            "used to get the recently listed properties".
        two_weeks (datetime.date): the starting date of the last two weeks. 
        search_time_span (dict): contains all the dates necessary for the scraping
            session.
          
    """
    name = "realtor_scraper"
    allowed_domains = ["www.realtor.com"]
    WEBSITE ="https://www.realtor.com"
    Primary_API = WEBSITE + "/api/v1/rdc_search_srp?client_id=rdc-search-for-sale-search&schema=vesta"
    RESULTS_PER_PAGE = 42
    page_requests_sent = 0
    page_requests_received = 0
    Secondary_API = WEBSITE+"/api/v1/hulk?client_id=detail-pages&schema=vesta"
    listings_requests_sent = 0
    listings_requests_received = 0
    pages_available:int
    results_available:int
    
    def __init__(self, crawler, scrape_all: Literal["True","False"], listing_type: Literal ["new_listings", "all_for_sale", "sold_listings"]):
        """
        Initialize the spider with custom parameters.
        """
        super().__init__()
        
        self.crawler = crawler
        self.settings = self.crawler.settings
        self.crawler.request_batch_delay = time()
        self.batch_size = self.settings.get('CONCURRENT_REQUESTS', 100)
        self.input_file = self.settings.get('INPUT_FILE', "realtor inputs.txt")
        self.listing_type = listing_type
        self.scrape_all = eval(scrape_all)
        
        self.today = date.today()
        self.yesterday = self.today - timedelta(days = 1)
        self.two_weeks = self.today - timedelta(days = 15)
        self.search_time_span = {    
            "sold_listings":self.today,
            "new_listings":self.yesterday,
            "all_for_sale":self.two_weeks
            }


    @classmethod
    def from_crawler(cls, crawler, scrape_all: Literal["True","False"], listing_type: Literal ["new_listings", "all_for_sale", "sold_listings"]):
        """
        Create a new instance of the spider from the crawler.
        Connects the spider's get_next_state method to the spider_idle signal.
        """
        spider = cls(crawler, scrape_all, listing_type) 
        crawler.signals.connect(spider.get_next_state, signal=signals.spider_idle)  
        return spider
           
    def get_next_state(self):
        """
        Prepare the spider to scrape the next state.
        If there are states left to scrape, continue crawling. Otherwise, allow the spider to close.
        """
        self.__delete_the_scraped_state()
        with open(self.input_file, "r") as f:
            contents = f.read()
        if contents:
            self.crawler.engine.crawl(self.gen_requests())
            raise DontCloseSpider 
        else:
            return
    
    
    def get_initial_variables(self):
        """
        Set up initial variables before starting the requests.
        """
        if self.scrape_all or self.input_file not in os.listdir(): 
            self.__write_states_to_the_input_file(STATES)
            print(f"\nscraping all  the states")
        self.__get_state_name__code__listing_type()
    
        
    def start_requests(self):
        """
        Start the initial requests for scraping.
        """
        self.state["today"] = self.today   
        self.state["yesterday"] = self.yesterday   
        self.state["two_weeks"] = self.two_weeks   
        self.state["search_time_span"] = self.search_time_span
        self.state["listing_type"] = self.listing_type
        yield self.gen_requests()
    
    def gen_requests(self):
        self.get_initial_variables()
        print(f'{'='*50}')
        print(f"\nscraping {self.state["listing_type"]} in {self.state["state_name"]} state.")
        self.page_requests_sent +=1
        headers, payload = self.__configure_primary_requests(1)
        return scrapy.Request(url=self.Primary_API, headers=headers, body=payload, method="POST", callback=self.run_primary_requests)

    
    def load_primary_requests_list(self,pages_available):
        """
        Load the list of primary requests to be made.
        """
        return [
            {"headers": headers, "payload": payload} 
            for page_number in range(2, pages_available + 1) 
            for headers, payload in [self.__configure_primary_requests(page_number)]
        ]

            
    def run_primary_requests(self, response): 
        """
        Process the response from the primary API requests.
        """
        self.__get_pages_available(response)
        yield from self.run_secondary_requests(response)
        
        print(f"\n\nprimary_stage found {self.state["results_available"]} {self.state["listing_type"]} properties in {self.state["pages_available"]} pages. ") 
        self.crawler.total_requests_count = (self.state["pages_available"] + self.state["results_available"]) - self.page_requests_sent
        print(f"total requests to make: {self.crawler.total_requests_count}")
        
        for request in self.load_primary_requests_list(self.state["pages_available"]):
            self.page_requests_sent +=1
            yield scrapy.Request(url=self.Primary_API, headers=request["headers"], body=request["payload"], method="POST", callback=self.run_secondary_requests)  
 
        
    def run_secondary_requests(self, response):
        """
        Process the response from the secondary API requests.
        """
        j_listings_prime_data = jmespath.search("data.home_search.properties",response.json())    
        self.page_requests_received +=1
        for listing in j_listings_prime_data:
            self.listings_requests_sent +=1
            headers, payload = self.__configure_secondary_requests(listing)
            yield scrapy.Request(url=self.Secondary_API, headers=headers, body=payload, method="POST", callback=self.parse)
           

    def parse(self,response):
        """
        Parse the detailed listing data from the secondary API response.
        """
        listing_data_item = RealtorItemLoader(Listing_Item(), selector= response)
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
        """
        Calculate the number of pages available based on the results returned.
        """
        results_available = response.json()["data"]["home_search"]["total"]
        
        if results_available%self.RESULTS_PER_PAGE == 0:
            pages_available = int(results_available/self.RESULTS_PER_PAGE)
        else:
            pages_available = int((results_available/self.RESULTS_PER_PAGE)+1)
        self.state["results_available"] = results_available
        self.state["pages_available"] = pages_available
        
           
    def __configure_primary_requests(self, page_number):
        """
        Configure the headers and payload for primary API requests.
        """
        headers = {}
        primary_request_data = PRIMARY_REQUEST_DATA.copy() 
        headers["referer"] = primary_request_data[self.state["listing_type"]]["referer"]\
            .replace("....", self.state["state_name"])\
            .replace("*",str(page_number))
        payload = primary_request_data[self.state["listing_type"]]["payload"]\
            .replace("**",self.state["state_name"])\
            .replace("--", self.state_code)\
            .replace("==", str(self.state["search_time_span"][self.state["listing_type"]] ))\
            .replace("++",str((page_number-1)*self.RESULTS_PER_PAGE))
        
        return headers, payload
    
    
    def __configure_secondary_requests(self, request_data):
        """
        Configure the headers and payload for secondary API requests.
        """
        headers = {}
        headers["referer"] = f"{self.WEBSITE}/realestateandhomes-detail/{request_data["permalink"]}"
        payload = SECONDARY_PAYLOAD\
            .replace("**", str(request_data["property_id"]))\
            .replace("++", str(request_data["listing_id"]))
        return headers, payload
    
    def __write_states_to_the_input_file(self, states):
        """
        Write the list of states to the input file.
        """
        with open(self.input_file,"w") as f:
            for state_name in states:
                f.write(f"{state_name}\n")
            
    def __get_state_name__code__listing_type(self):
        """
        Retrieve the state name, code, and listing type from the input file.
        """
        with open(self.input_file, "r") as f:
            contents = f.read()
        if contents:
            states_names_and_codes = dict(zip(STATES, STATES_CODES))
            self.state["state_name"] = contents.split("\n")[0].strip().replace(" ","-").lower()
            self.state_code = states_names_and_codes[self.state["state_name"].lower()]
        else:
            raise ValueError('the input file "realtor inputs.txt" is empty!')    
        
    
    def __delete_the_scraped_state(self):
        """
        Delete the already scraped state from the input file.
        """
        with open(self.input_file,"r") as f:
            all_states = [state_name.strip().lower().replace(" ","-") for state_name in f.read().strip().split("\n")]
        if all_states[0].strip() == self.state["state_name"].strip():
            all_states.remove(self.state["state_name"])
            self.__write_states_to_the_input_file(all_states)
        else:
            print(f'\nall_states: {all_states}\nself.state["state_name"]: {self.state["state_name"]}\n')
            raise ValueError(f'the first state in the "{self.input_file}" does not match the scraped state {self.state["state_name"]}!') 
        