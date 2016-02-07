# -*- coding: utf-8 -*-
import scrapy
import re
import datetime
from scrapy_openlife.items import *
PATT_DATE = re.compile(r'\d\d\d\d-\d\d-\d\d')


class OpenlifeSpider(scrapy.Spider):
    name = "openlife"
    allowed_domains = ["openlife.pl"]
    start_urls = (
        'https://portal.openlife.pl/frontend/login.html',
    )
    def parse(self, response):
        login = password = None
        with open("credentials") as f:
            login, password = f.readlines()
            login, password = login.strip(), password.strip()
        return [scrapy.FormRequest.from_response(response,
                    formdata={'j_username': login, 'j_password': password},
                    callback=self.after_login)]

    def after_login(self, response):
        # check login succeed before going on
        if "Niepoprawny identyfikator" in response.body:
            self.log("Login failed", level=scrapy.log.ERROR)
            return
        yield scrapy.Request('https://portal.openlife.pl/frontend/secure/policyList.html',
                             callback=self.on_policy_list)

    def on_policy_list(self, response):
        policyurl = response.xpath("//a[contains(@href, 'idPolicy')]/@href").extract()[0]
        policyurl = response.urljoin(policyurl)
        yield scrapy.Request(policyurl, callback=self.do_policy)


    def do_policy(self, response):
        # for this day:
        entries = response.xpath("//table[@id='tabRCY']/tbody/tr")
        maxdate = None
        for entry in entries:
            fields = [e.extract().strip() for e in entry.xpath('td/text()')]
            name, amount, unitprice, value, currency = fields
            pricedate = entry.xpath('td/nobr/text()')[0].extract().strip()
            pricedate = PATT_DATE.search(pricedate).group(0)
            amount, unitprice, value = [float(e.replace(',', '.').replace(u'\xa0', '')) for e in [amount, unitprice, value]]
            item = ScrapyOpenlifeItem()
            item['name'] = name
            item['amount'] = amount
            item['unitprice'] = unitprice
            item['value'] = value
            item['currency'] = currency
            item['pricedate'] = pricedate
            yield item
            maxdate = max(maxdate, pricedate)
        maxdate = datetime.datetime.strptime(maxdate, "%Y-%m-%d").date()
        prevday = (maxdate - datetime.timedelta(1)).strftime("%Y-%m-%d")
        if '2016' in prevday:
            yield scrapy.FormRequest.from_response(response,
                    formdata={'showFromDate': prevday},
                    callback=self.do_policy)
        # import pdb; pdb.set_trace()
        # from scrapy.shell import inspect_response; inspect_response(response, self)

