# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import sqlite3

class ScrapyOpenlifePipeline(object):
    def process_item(self, item, spider):
        return item

class DbPipeline(object):
    def __init__(self):
        self.con = None

    def open_spider(self, spider):
        self.con = sqlite3.connect('data.db')
        self.con.text_factory = str
        self.con.execute("CREATE TABLE IF NOT EXISTS datapoints "
                         "(name TEXT, amount REAL, unitprice REAL, pricedate TEXT, value REAL, currency TEXT,"
                         "UNIQUE (name, pricedate))")


    def close_spider(self, spider):
        self.con.close()

    def process_item(self, item, spider):
        self.con.execute("INSERT INTO datapoints VALUES (?,?,?,?,?,?)",
                         (item['name'],
                          item['amount'],
                          item['unitprice'],
                          item['pricedate'],
                          item['value'],
                          item['currency']))
        self.con.commit()
        return item
