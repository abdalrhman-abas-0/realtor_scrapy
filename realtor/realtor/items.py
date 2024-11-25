"""
Realtor Scraper Items

This module defines the models for the items scraped from Realtor.com.
It includes the definition of the Listing_Item class which represents the data structure for each listing,
and the RealtorItemLoader class for processing item data during the scraping process.
"""

import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Join, Identity
from scrapy.loader import ItemLoader

class RealtorItemLoader(ItemLoader):
    """
    Custom ItemLoader for processing scraped data.
    The default output processor is set to TakeFirst, which retrieves the first non-null/non-empty value from the list of values.
    """
    default_output_processor = TakeFirst()

class Listing_Item(scrapy.Item):
    """
    Data model for the real estate listings scraped from Realtor.com.
    Each field represents a piece of information about a listing.
    """
    state = scrapy.Field()
    price = scrapy.Field()
    URL = scrapy.Field()
    property_id = scrapy.Field()
    listing_id = scrapy.Field()
    type = scrapy.Field()
    year_built = scrapy.Field()
    street = scrapy.Field()
    city = scrapy.Field()
    state_code = scrapy.Field()
    zip_code = scrapy.Field()
    bedrooms = scrapy.Field()
    bathrooms = scrapy.Field()
    sqft = scrapy.Field()
    parameter = scrapy.Field()
    agent = scrapy.Field()
    office = scrapy.Field()
    agent_email = scrapy.Field()
    office_email = scrapy.Field()
    sold_date = scrapy.Field()
    status = scrapy.Field()
    days_on_realtor = scrapy.Field()
