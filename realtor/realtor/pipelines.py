# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exporters import JsonItemExporter, CsvItemExporter, JsonLinesItemExporter
from scrapy.utils.project import get_project_settings
from datetime import datetime, date
import pandas as pd
import numpy as np
from datetime import datetime 
import os
from time import time, sleep
from scrapy import signals
from typing import Literal


class Realtor_Pipeline:
    pbar = None
    only_running_the_last_request = True
    file_name = None
    last_saved_state = ""
    
    def __init__(self, crawler):
        self.crawler = crawler 
        self.save_points_dir = crawler.settings.get("SAVE_POINTS_DIR", "crawls/temporary_save_points") 

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls(crawler=crawler)
        crawler.signals.connect(pipeline.spider_closed, signal=signals.spider_closed)
        return pipeline
    
    
    def create_save_point_file(self, spider):
        self.file_name = f"{spider.name} temporary {spider.state["listing_type"]} {spider.state["today"]}.jsonl"
        self.file = open(os.path.join(self.save_points_dir,self.file_name), 'ab')
        self.exporter = JsonLinesItemExporter(self.file)
        self.exporter.start_exporting()
    
    
    def process_item(self, item, spider):
        if "exporter" not in dir(self):
            self.create_save_point_file(spider)
            
        adapter = ItemAdapter(item)
        adapter["price"] = int(adapter["price"]) if adapter.get("price") else np.nan
        adapter["status"] = adapter["status"].lower() if adapter["status"] else adapter["status"]
        if (sold_date_str:=adapter.get("sold_date")):
            sold_date = datetime.strptime(sold_date_str, "%Y-%m-%d").date()
            adapter["days_on_realtor"] = (spider.state["today"] - sold_date).days
            adapter["sold_date"] = sold_date.strftime("%d/%m/%Y")
        self.exporter.export_item(item)
    
    def construct_df_from_temporary_file(self, spider):
        df = pd.read_json(os.path.join(self.save_points_dir,self.file_name),lines= True)
        df.drop_duplicates(inplace=True)
        return df
    
    def save_outputs(self, spider):
        df = self.construct_df_from_temporary_file(spider)
        # TODO: groupe the states together and save each group in it's 
        # separate excel file
        output_dir = self.crawler.settings.get("OUTPUT_DIR", "realtor/outputs")
        states_scraped_list = list(df["state"].unique())
        print(f"\npipeline.states_scraped_list: {states_scraped_list}")
        for state in states_scraped_list:
            state_df = df[df["state"] == state]
            file_name = f"{spider.name} {spider.state["listing_type"]} {state}.xlsx"
            file_path = os.path.join(output_dir,file_name)
            state_df.to_excel(file_path, index=False)
            print(f"-->results of {state}:{state_df.shape[0]}")
       
        
    def spider_closed(self, spider, reason):
        try:
            self.exporter.finish_exporting()
            self.file.close()
        except:
            pass
            
        if reason == "finished":
            self.save_outputs(spider)
            # deleting the primary save_point file
            os.remove(os.path.join(self.save_points_dir,self.file_name))
     
      
       
    
    
    
