"""
Module to dynamically extract HTTP request headers by simulating user interaction on realtor.com.
This module uses Selenium WebDriver with stealth techniques to bypass bot detection and intercepts
network requests to construct valid headers for API requests.

Typical usage example:

    GetHeaders: Handles the extraction of headers from network requests.
    update_headers = GetHeaders()
    headers = update_headers.fresh_headers("alabama", 60)
"""

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

from seleniumwire import webdriver
from selenium_stealth import stealth
from time import sleep
import random
from fake_useragent import UserAgent
from typing import Dict, Optional


class GetHeaders:
    """
    A class to extract headers dynamically by intercepting network requests using Selenium WebDriver.
    Designed specifically for requests to realtor.com.

    Attributes:
        extracted (bool): Flag indicating whether headers have been successfully extracted.
        first_option (list): List of headers captured using the first option strategy.
        second_option (list): List of headers captured using the second option strategy.
        headers_template (dict): Template for constructing HTTP headers with common fields.
        API (str): URL of the API endpoint being monitored.
        payload_sample (str): Partial string used to identify specific API requests by their payload.
        g_accounts_iframe (str): URL pattern used to identify Google account-related requests.
    """

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

    payload_sample = "{\"query\":\"\\n  query ConsumerSearchQuery(\\n    $query: HomeSearchCriteria!\\n    $limit: Int\\n    $offset: Int\\n"
    g_accounts_iframe = "https://accounts.google.com/o/oauth2/iframe#origin=https"

    def __initiate_browser(self, user_agent: str) -> None:
        """
        Initializes a Chrome WebDriver with specific options and stealth mode.

        Args:
            user_agent (str): The user agent string to set in the browser.
        """
        options = Options()
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-proxy-certificate-handler")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        prefs = {"profile.default_content_setting_values.geolocation": 2}
        options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(options=options)

        self.user_agent = user_agent
        stealth(self.driver,
                user_agent=self.user_agent,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )

    def __construct_headers(self, request_headers: Dict[str, str], first_option: bool, quit_browser: bool) -> None:
        """
        Constructs headers from intercepted request headers and stores them.

        Args:
            request_headers (dict): The headers intercepted from a request.
            first_option (bool): Determines whether to save headers to the first option list.
            quit_browser (bool): Indicates whether the browser should quit after this step.
        """
        headers = self.headers_template.copy()
        headers.update({
            "user-agent": request_headers["user-agent"],
            "traceparent": request_headers["traceparent"],
            "tracestate": request_headers["tracestate"],
            "newrelic": request_headers["newrelic"],
            "referer": request_headers["referer"],
        })
        if first_option:
            self.first_option.append(headers)
        else:
            self.second_option.append(headers)
        if quit_browser:
            self.extracted = True

    def __requests_interceptor__(self, request) -> None:
        """
        Intercepts network requests made by the browser and processes headers if conditions match.
        """
        if request.path.endswith(('.png', '.jpg', '.gif')) or "google" in request.url:
            request.abort()
        else:
            request_headers = dict(request.headers)
            try:
                request_body = request.body.decode("utf-8")
            except Exception:
                request_body = None
            if self.API in request.url and self.payload_sample in request_body:
                self.API = request.url
                self.__construct_headers(request_headers, True, True)
            elif request_headers.get("newrelic") and request_headers.get("traceparent") and request_headers.get("tracestate"):
                self.API = request.url
                self.__construct_headers(request_headers, False, False)

    def __requests_inspector(self) -> Dict[str, str]:
        """
        Inspects intercepted requests to find matching headers.

        Returns:
            dict: The headers of a matching request.

        Raises:
            ValueError: If no headers are found.
        """
        for request in self.driver.requests:
            if not request.response:
                continue
            request_headers = dict(request.headers)
            try:
                request_body = request.body.decode("utf-8")
            except Exception:
                request_body = None
            if self.API in request.url and not self.extracted and self.payload_sample in request_body:
                self.API = request.url
                self.__construct_headers(request_headers, True, False)
            elif request_headers.get("newrelic") and request_headers.get("traceparent") and request_headers.get("tracestate"):
                self.__construct_headers(request_headers, False, False)

        if self.first_option:
            return self.first_option[-1]
        elif self.second_option:
            return self.second_option[-1]
        else:
            raise ValueError("Headers are not found!")

    def __run(self, state: str, wait_period: int = 180) -> Dict[str, str]:
        """
        Runs the header extraction process for a given state.

        Args:
            state (str): The state for which to extract headers.
            wait_period (int): The maximum wait time for web elements to load.

        Returns:
            dict: The extracted headers.
        """
        self.driver.request_interceptor = self.__requests_interceptor__
        url = f"https://www.realtor.com/realestateandhomes-search/{state}/show-recently-sold"

        try:
            self.driver.get(url)
        except Exception:
            pass

        headers = self.__requests_inspector() if not self.extracted else self.first_option[-1]
        self.driver.quit()
        return headers

    def fresh_headers(self, state: str = "", wait_period: int = 180) -> Dict[str, str]:
        """
        Generates fresh headers by simulating user interaction on realtor.com.

        Args:
            state (str): The state to scrape headers for.
            wait_period (int): The maximum wait time for web elements to load.

        Returns:
            dict: The extracted headers.
        """
        ua = UserAgent(os="macos", browsers="chrome")
        while True:
            try:
                self.__initiate_browser(ua.random)
                headers = self.__run(state or random.choice(["Texas", "New-York", "Florida", "New-Jersey", "California"]), wait_period)
                break
            except Exception:
                try:
                    self.driver.quit()
                except Exception:
                    pass
                sleep(random.uniform(60, 180))
        return headers
