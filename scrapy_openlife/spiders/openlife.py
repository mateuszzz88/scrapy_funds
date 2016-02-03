# -*- coding: utf-8 -*-
import scrapy


class OpenlifeSpider(scrapy.Spider):
    name = "openlife"
    allowed_domains = ["openlife.pl"]
    start_urls = (
        'http://www.openlife.pl/',
    )

    def parse(self, response):
        pass
