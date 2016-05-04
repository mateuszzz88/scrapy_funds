# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapyOpenlifeItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    name = scrapy.Field()
    amount = scrapy.Field()
    unitprice = scrapy.Field()
    pricedate = scrapy.Field()
    value = scrapy.Field()
    currency = scrapy.Field()
    policy = scrapy.Field()


class ScrapyOpenlifeHistoryItem(scrapy.Item):
    id = scrapy.Field()
    amount = scrapy.Field()
    type = scrapy.Field()
    date = scrapy.Field()
    policy = scrapy.Field()

