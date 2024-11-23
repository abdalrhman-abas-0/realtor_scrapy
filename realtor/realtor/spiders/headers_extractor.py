from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options

from seleniumwire import webdriver 
from selenium_stealth import stealth
from time import sleep
import random
from fake_useragent import UserAgent
import random
from typing import Literal



class Get_Headers:
    extracted = False
    first_option = []
    second_option = []
    headers_template = {
        "host": "www.realtor.com",
        "accept": "application/json, text/javascript",
        "accept-language": "en-US,en;q=0.5",
        "accept-encoding": "gzip, deflate, br",
        "content-type": "application/json",
        "rdc-ab-test-client": "rdc-search-for-sale",
        "origin": "https://www.realtor.com",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "connection": "keep-alive",
     
    }
    API = "https://www.realtor.com/api/v1/rdc_search_srp?client_id=rdc"
    "https://www.realtor.com/rdc_user_check/xhr/api/v2/collector"
    
    payload_sample = "{\"query\":\"\\n  query ConsumerSearchQuery(\\n    $query: HomeSearchCriteria!\\n    $limit: Int\\n    $offset: Int\\n"
    g_accounts_iframe="https://accounts.google.com/o/oauth2/iframe#origin=https"

        
        
    def __initiate_browser(self, user_agent):
        options = Options()
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-proxy-certificate-handler")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        prefs = {"profile.default_content_setting_values.geolocation" :2}
        options.add_experimental_option("prefs",prefs)
        self.driver = webdriver.Chrome(options= options )

        self.user_agent = user_agent
        stealth(self.driver,
        user_agent= self.user_agent,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )

 
    def __construct_headers(self,request_headers:dict, first_option:bool, quit_browser:bool):
        headers = self.headers_template.copy()
        headers["user-agent"] = request_headers["user-agent"]
        headers["traceparent"] = request_headers["traceparent"]
        headers["tracestate"] = request_headers["tracestate"]
        headers["newrelic"] = request_headers["newrelic"]
        headers["referer"] = request_headers["referer"] 
        if first_option:  
            self.first_option.append(headers)
        else:
            self.second_option.append(headers)
        if quit_browser:
            self.extracted = True

    def __requests_interceptor__(self, request):
        if request.path.endswith(('.png', '.jpg', '.gif')) or "google" in request.url:
            request.abort()
        elif "google" in request.url:
            request.abort()
        else:
            request_headers = dict(request.headers)
            try:
                request_body = request.body.decode("utf-8")
            except:
                request_body = None 
            if self.API in request.url and self.payload_sample in request_body :
                self.API = request.url
                request_headers = dict(request.headers)
                self.__construct_headers(request_headers, True, True)
      
                
            elif request_headers.get("newrelic") and request_headers.get("traceparent") and request_headers.get("tracestate"):
                self.API = request.url
                request_headers = dict(request.headers)
                self.__construct_headers(request_headers, False, False)
           
                
    def __requests_inspector(self):
        for request in self.driver.requests:
            if not request.response:
                continue
            
            request_headers = dict(request.headers)
            try:
                request_body = request.body.decode("utf-8")
            except:
                request_body = None 
            if self.API in request.url and not self.extracted and self.payload_sample in request_body :
                print("\ncaptured a request A2 -----------")
                self.API = request.url
                request_headers = dict(request.headers)
                self.__construct_headers(request_headers, True, False)
            
            elif request_headers.get("newrelic") and request_headers.get("traceparent") and request_headers.get("tracestate"):
                print("\ncaptured a request B2 -----------")
                self.API = request.url
                request_headers = dict(request.headers)
                self.__construct_headers(request_headers, False, False)
                
        if self.first_option:
            return self.first_option[-1]
        elif self.second_option:
            return self.second_option[-1]
        else:
            raise ValueError("headers are not found!!")
                
    def __run(self,state:str, wait_period:int=180):

        self.driver.request_interceptor = self.__requests_interceptor__
        # url = f"https://www.realtor.com/realestateandhomes-search/{state}"
        url = f"https://www.realtor.com/realestateandhomes-search/{state}/show-recently-sold"
        # first page
        sleep(random.uniform(3, 7))
        try:
            print("entering the website---------")
            self.driver.get(url)
        except:
            pass
        
        if not self.extracted:
            try:
                clear_sold_option = WebDriverWait(self.driver, wait_period).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="filter-dropdown-listingStatus"] svg[data-testid="icon-clear-filled"]'))
                    )
                ActionChains(self.driver).send_keys(Keys.END).perform()
                sleep(random.uniform(3, 6))
                ActionChains(self.driver).move_to_element(clear_sold_option)
            except:
                pass
        
        if not self.extracted:
            try:
                sleep(random.uniform(20, 60))
                WebDriverWait(self.driver, wait_period).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="filter-dropdown-listingStatus"]'))
                    )
                ActionChains(self.driver).send_keys(Keys.END).perform()
                ActionChains(self.driver).send_keys(Keys.HOME).perform()
            except:
                pass
        
        if not self.extracted:
            try:
                sleep(random.uniform(2, 5))
                next_page = WebDriverWait(self.driver, wait_period).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[aria-label="pagination"] > a[aria-label="Go to next page"]'))
                    )
                ActionChains(self.driver).move_to_element(next_page)
                sleep(random.uniform(0.5, 2))
                next_page.click()  
            except:
                pass
            
        
        if not self.extracted:
            try:
                sleep(random.uniform(30, 60))
                WebDriverWait(self.driver, wait_period).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="filter-dropdown-listingStatus"]'))
                    )
                ActionChains(self.driver).send_keys(Keys.END).perform()
                sleep(2.1)
                ActionChains(self.driver).send_keys(Keys.HOME).perform()
            except:
                pass
        
        
        if not self.extracted:
            sleep(random.uniform(10, 50))
            print("\n\nprocedures concluded\n\n")
            headers = self.__requests_inspector()
        else:
            headers = self.first_option[-1]
             
        self.driver.quit()
        return headers
        
    def fresh_headers(self, state:str="", wait_period:int=180):
        ua = UserAgent(os="macos", browsers="chrome")
        while True:
            if not state:
                state = random.choice(["Texas","New-York", "Florida", "New-Jersey", "California"])
                try:
                    self.__initiate_browser(ua.random)
                    headers = self.__run(state, wait_period) 
                    print("obtained the headers successfully.")
                    break
                except:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    print("failed getting headers!!")
                    sleep(random.uniform(60, 180))
                    state = ""
        return headers
    
    
if __name__ == "__main__":
    print(Get_Headers().fresh_headers("alabama", 60))  