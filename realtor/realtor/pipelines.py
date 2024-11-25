"""
This module defines the item pipeline for processing, exporting, and saving data scraped by a Scrapy spider.
It is designed for realtor.com scraping projects and includes functionality to:
- Create temporary save-point files during the scraping process.
- Process and clean scraped data.
- Export data to JSON lines and Excel files for analysis.

Classes:
    Realtor_Pipeline: Handles processing, exporting, and managing scraped data during and after spider execution.
"""

from itemadapter import ItemAdapter
from scrapy.exporters import JsonLinesItemExporter
from scrapy.utils.project import get_project_settings
from datetime import datetime, date
import pandas as pd
import numpy as np
import os
from time import time, sleep
from scrapy import signals
from typing import Literal


class Realtor_Pipeline:
    """
    A Scrapy pipeline for handling scraped items, managing temporary save-points, and exporting data.

    Attributes:
        only_running_the_last_request (bool): Flag to determine if only the last request is being handled.
        file_name (Optional[str]): Name of the temporary save-point file for the current spider run.
        last_saved_state (str): Name of the last processed state in the scraping process.
    """
    only_running_the_last_request = True
    file_name = None
    last_saved_state = ""

    def __init__(self, crawler):
        """
        Initializes the pipeline with a reference to the Scrapy crawler and the save-points directory.

        Args:
            crawler (scrapy.crawler.Crawler): The Scrapy crawler instance.
        """
        self.crawler = crawler
        self.save_points_dir = crawler.settings.get("SAVE_POINTS_DIR", "crawls/temporary_save_points")

    @classmethod
    def from_crawler(cls, crawler):
        """
        Factory method to create a pipeline instance from a Scrapy crawler.

        Args:
            crawler (scrapy.crawler.Crawler): The Scrapy crawler instance.

        Returns:
            Realtor_Pipeline: An instance of the pipeline.
        """
        pipeline = cls(crawler=crawler)
        crawler.signals.connect(pipeline.spider_closed, signal=signals.spider_closed)
        return pipeline

    def create_save_point_file(self, spider):
        """
        Creates a temporary save-point file for storing scraped items during the spider's execution.

        Args:
            spider (scrapy.Spider): The Scrapy spider instance.
        """
        self.file_name = f"{spider.name} temporary {spider.state['listing_type']} {spider.state['today']}.jsonl"
        self.file = open(os.path.join(self.save_points_dir, self.file_name), 'ab')
        self.exporter = JsonLinesItemExporter(self.file)
        self.exporter.start_exporting()

    def process_item(self, item, spider):
        """
        Processes each scraped item, cleans data, and writes it to the temporary save-point file.

        Args:
            item (dict): The scraped item.
            spider (scrapy.Spider): The Scrapy spider instance.

        Returns:
            dict: The processed item.
        """
        if "exporter" not in dir(self):
            self.create_save_point_file(spider)

        adapter = ItemAdapter(item)
        adapter["price"] = int(adapter["price"]) if adapter.get("price") else np.nan
        adapter["status"] = adapter["status"].lower() if adapter["status"] else adapter["status"]
        if (sold_date_str := adapter.get("sold_date")):
            sold_date = datetime.strptime(sold_date_str, "%Y-%m-%d").date()
            adapter["days_on_realtor"] = (spider.state["today"] - sold_date).days
            adapter["sold_date"] = sold_date.strftime("%d/%m/%Y")
        self.exporter.export_item(item)
        return item

    def construct_df_from_temporary_file(self, spider):
        """
        Constructs a Pandas DataFrame from the temporary save-point file.

        Args:
            spider (scrapy.Spider): The Scrapy spider instance.

        Returns:
            pandas.DataFrame: DataFrame containing the scraped data.
        """
        df = pd.read_json(os.path.join(self.save_points_dir, self.file_name), lines=True)
        df.drop_duplicates(inplace=True)
        return df

    def save_outputs(self, spider):
        """
        Saves the processed data into Excel files, one for each state scraped, in the output directory.

        Args:
            spider (scrapy.Spider): The Scrapy spider instance.
        """
        df = self.construct_df_from_temporary_file(spider)
        output_dir = self.crawler.settings.get("OUTPUT_DIR", "realtor/outputs")
        states_scraped_list = list(df["state"].unique())
        print(f"\npipeline.states_scraped_list: {states_scraped_list}")
        for state in states_scraped_list:
            state_df = df[df["state"] == state]
            file_name = f"{spider.name} {spider.state['listing_type']} {state}.xlsx"
            file_path = os.path.join(output_dir, file_name)
            state_df.to_excel(file_path, index=False)
            print(f"-->results of {state}:{state_df.shape[0]}")

    def spider_closed(self, spider, reason):
        """
        Handles actions to perform when the spider is closed, such as exporting data and cleaning up.

        Args:
            spider (scrapy.Spider): The Scrapy spider instance.
            reason (str): The reason for spider closure (e.g., "finished", "canceled").
        """
        try:
            self.exporter.finish_exporting()
            self.file.close()
        except Exception:
            pass

        if reason == "finished":
            self.save_outputs(spider)
            # Deleting the primary save-point file
            os.remove(os.path.join(self.save_points_dir, self.file_name))
