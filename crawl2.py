#!/usr/bin/env python
# http://doc.scrapy.org/en/latest/topics/practices.html

import fundsreport.settings
import django, django.conf
djangosettingsdict = {key: value for (key, value) in fundsreport.settings.__dict__.iteritems() if '__' not in key}
django.conf.settings.configure(django.conf.global_settings, **djangosettingsdict)
django.setup()

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from crawler.scrapy_openlife.spiders.openlife_details import OpenlifeDetailsSpider

import crawler.scrapy_openlife.settings as settingsmod
settings = get_project_settings()
settings.setmodule(settingsmod)
process = CrawlerProcess(settings)

process.crawl(OpenlifeDetailsSpider)
process.start()  # the script will block here until the crawling is finished
