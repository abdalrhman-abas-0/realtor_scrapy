# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Join, Identity
from scrapy.loader import ItemLoader


class RealtorItemLoader(ItemLoader):
    default_output_processor = TakeFirst()
 
class Listing_Item(scrapy.Item):
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
    days_on_realtor = scrapy.Field()###################
    
    

   