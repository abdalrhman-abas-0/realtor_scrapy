# REALTOR_SCRAPY

## Overview

- scrapes real estate listings from Realtor.com using a Scrapy framework to handle the web crawling and data extraction processes.
- it scrapes the recently sold properties, the properties listed for sale recently (within the last 24 hours) and all the properties listed for sale (within the last 15 days).
- the states to be scraped should be manually provided in the "realtor inputs.txt" input file.
-the xlsx output file will be saved in the outputs directory.

## Usage:
### Inputs:
#### States:
- scraping a one or more states: provide the names of these states in the txt input file "realtor inputs.txt" and input `False` in the `scrape_all` argument when running the spider.
- scraping all the states: empty the txt input file and input `True` in the `scrape_all` argument when running the spider.

#### Listings Type:
- the `listing_type` argument is used to choose the type of listings to be scraped depending on the input which can only be one of the next 3 choices.
    - `new_listings` : scrapes the recently listed properties "with in the last 24 hours".
    - `all_for_sale` : scrapes the all properties listed with in the two weeks. 
    - `sold_listings` : scrapes the recently sold properties "with in the last 24 hours". 

### Running The Spider:
#### through the terminal:
```bash
scrapy crawl realtor_scraper -a scrape_all=False -a listing_type= new_listings
```
#### through a script:
```python
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from realtor.spiders.realtor_scraper import RealtorScraperSpider

settings = get_project_settings()
process = CrawlerProcess(settings)
process.crawl(RealtorScraperSpider, scrape_all="True", listing_type="sold_listings")
process.start()
process.stop()
```

### Outputs:
- the outputs are saved in a xlsx file for each state and listing type "search" and the file can be found in the `outputs` folder.
- each listing should have the following data:
    - state
    - price
    - URL
    - property_id
    - listing_id
    - type
    - year_built
    - street
    - city
    - state_code
    - zip_code
    - bedrooms
    - bathrooms
    - sqft
    - parameter
    - agent
    - office
    - agent_email
    - office_email
    - status
    - sold_date
    - days_on_realtor


## Technologies Used

- **Python 3.x**: The main programming language used for the scraper.
- **Scrapy**: Web scraping framework used to get, clean and save the scraped data.
- **Pandas**: Data manipulation library used to manage and save the data.

## Installation
- run the following command.
```bash
git clone https://github.com/abdalrhman-abas-0/realtor_scrapy.git
cd realtor_scrapy
```
### Setup
- to install the needed packages use the "requirements.txt" file :
```bash
pip install -r requirements.py
```

## File Structure

```bash
├───realtor
│   ├───realtor
│   │   ├───crawl_jobs
│   │   │   ├───realtor_spider_job
│   │   │   └───temporary_save_points
│   │   ├───outputs
│   │   ├───spiders
│   │   │   ├───__init__.py
│   │   │   ├───headers_extractor.py
│   │   │   ├───realtor_scraper.py
│   │   │   └───scraping headers.txt
│   │   ├───__init__.py
│   │   ├───constants.py
│   │   ├───items.py
│   │   ├───middlewares.py
│   │   ├───pipelines.py
│   │   └───settings.py
│   ├───realtor inputs.txt
│   └───scrapy.cfg
├───.gitignore
├───readme.md
└───requirements.txt
```