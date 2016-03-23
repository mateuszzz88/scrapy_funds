# -*- coding: utf-8 -*-
import datetime
import re

from crawler.scrapy_openlife.items import *

PATT_DATE = re.compile(r'\d\d\d\d-\d\d-\d\d')


class OpenlifeSpider(scrapy.Spider):
    name = "openlife"
    allowed_domains = ["openlife.pl"]
    start_urls = (
        'https://portal.openlife.pl/frontend/login.html',
    )
    date_from = None

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
        self.date_from = self.get_last_date(response)
        yield scrapy.Request(policyurl, callback=self.do_policy)


    def do_policy(self, response):
        mindate = datetime.datetime.strptime(self.date_from, "%Y-%m-%d").date()
        maxdate = datetime.date.today()
        for day in daterange(mindate, maxdate):
            yield scrapy.FormRequest.from_response(response,
                    formdata={'showFromDate': day.strftime("%Y-%m-%d")},
                    callback=self.do_policy_day)

    def do_policy_day(self, response):
        # for this day:
        entries = response.xpath("//table[@id='tabRCY']/tbody/tr")
        for entry in entries:
            fields = [e.extract().strip() for e in entry.xpath('td/text()')]
            name, amount, unitprice, value, currency = fields
            name = name.encode('utf-8')
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

    def get_last_date(self, response):
        from report.models import DataPoint
        try:
            date = DataPoint.latest_date()
            date = datetime.datetime.strptime(date, "%Y-%m-%d").date() + datetime.timedelta(1)
            date = date.strftime("%Y-%m-%d")
        except:
            date = response.xpath("//table/tbody/tr/td[4]/text()")[0].extract().strip()
        return date


def daterange(start_date, end_date):
    from datetime import timedelta
    for n in range(int ((end_date - start_date).days)):
        day =  start_date + timedelta(n)
        if day.weekday() < 5:
            yield day

# import pdb; pdb.set_trace()
# from scrapy.shell import inspect_response; inspect_response(response, self)
