# -*- coding: utf-8 -*-
import datetime
import re
from report.models import Policy, PolicyOperation
from collections import defaultdict
from pprint import pprint as pp

from crawler.scrapy_openlife.items import *
import scrapy
PATT_DATE = re.compile(r'\d\d\d\d-\d\d-\d\d')


class OpenlifeSpider(scrapy.Spider):
    name = "openlife"
    allowed_domains = ["openlife.pl"]
    start_urls = (
        'https://portal.openlife.pl/frontend/login.html',
    )

    with open('/tmp/failed_nometa.txt', 'w'), open('/tmp/failed1.txt', 'w') as f1, open('/tmp/failed2.txt', 'w') as f2, open('/tmp/requested.txt', 'w') as r, open('/tmp/good.txt', 'w') as g:
        pass

    def parse(self, response):
        for policy in Policy.objects.filter(company='openlife'):
            login = policy.login
            password = policy.password
            yield scrapy.FormRequest.from_response(response,
                                                   formdata={'j_username': login, 'j_password': password},
                                                   callback=self.after_login,
                                                   meta={'policy': policy, 'cookiejar': policy, 'date_from': None},
                                                   dont_filter=True)

    def after_login(self, response):
        # check login succeed before going on
        if "Niepoprawny identyfikator" in response.body:
            self.log("Login failed", level=scrapy.log.ERROR)
            return
        yield scrapy.Request('https://portal.openlife.pl/frontend/secure/policyList.html',
                             callback=self.on_policy_list,
                             meta=reuse_meta(response),
                             dont_filter=True)

    def on_policy_list(self, response):
        policy_url = response.xpath(
            "//tr[td//text()[contains(., 'Plan Inwestycyjny Lepsze Jutro')]]//a[contains(@href, 'idPolicy')]/@href").extract()[0]
        policy_url = response.urljoin(policy_url)
        response.meta['date_from'] = self.get_last_date(response)
        yield scrapy.Request(policy_url, callback=self.do_policy,
                             meta=reuse_meta(response),
                             dont_filter=True)

    def do_policy(self, response):
        date_from = response.meta['date_from']
        min_date = datetime.datetime.strptime(date_from, "%Y-%m-%d").date()
        max_date = datetime.date.today()  # TODO this should be read from page/meta        max_date = datetime.date.today()  # TODO this should be read from page/meta

        yield scrapy.Request('https://portal.openlife.pl/frontend/secure/accountHistory.html',
                             callback=self.on_account_history,
                             meta=reuse_meta(response),
                             dont_filter=True)
        for day in daterange(min_date, max_date):
            yield scrapy.FormRequest.from_response(response,
                                                   formdata={'showFromDate': day.strftime("%Y-%m-%d")},
                                                   callback=self.do_policy_day,
                                                   meta=reuse_meta(response),
                                                   dont_filter=True)

    def do_policy_day(self, response):
        # for this day:
        entries = response.xpath("//table[@id='tabRCY']/tbody/tr")
        for entry in entries:
            fields = [e.extract().strip() for e in entry.xpath('td/text()')]
            name, amount, unitprice, value, currency = fields
            name = name.encode('utf-8')
            pricedate = entry.xpath('td/nobr/text()')[0].extract().strip()
            pricedate = PATT_DATE.search(pricedate).group(0)
            amount, unitprice, value = [float(e.replace(',', '.').replace(u'\xa0', '')) for e in
                                        [amount, unitprice, value]]

            item = ScrapyOpenlifeItem()
            item['name'] = name
            item['amount'] = amount
            item['unitprice'] = unitprice
            item['value'] = value
            item['currency'] = currency
            item['pricedate'] = pricedate
            item['policy'] = response.meta['policy']
            yield item

    def get_last_date(self, response):
        from report.models import DataPoint
        try:
            date = DataPoint.latest_date(response.meta['policy'])
            date = date + datetime.timedelta(1)
            date = date.strftime("%Y-%m-%d")
        except:
            date = response.xpath("//table/tbody/tr/td[4]/text()")[0].extract().strip()
            # on policy list: date_from = response.xpath("//div[@class='boxContent_lvl1']//tbody//td")[3].xpath('text()')[0].extract().strip()
        return date

    def on_account_history(self, response):
        nextpage = response.xpath("//a[@id='linkNextPage']/@href").extract()
        if nextpage:
            nextpage = nextpage[0].strip()
            nextpage = response.urljoin(nextpage)
            yield scrapy.Request(nextpage,
                                 callback=self.on_account_history,
                                 meta=reuse_meta(response))

        last_date = (PolicyOperation.latest_date(response.meta['policy'])
                     or datetime.date(year=2000, month=1, day=1)).strftime("%Y-%m-%d")
        entries = response.xpath("//div[@class='boxContent_lvl2']/div/table/tbody/tr")
        # self.debug(response)
        for entry in entries:
            fields = [e.extract().strip() for e in entry.xpath('td/text()')]
            _, op_id, op_date, op_type, op_amount, _, _, details, _ = fields
            op_type = op_type.encode('utf-8')
            op_amount = float(op_amount.replace(',', '.').replace(u'\xa0', ''))
            item = ScrapyOpenlifeHistoryItem()
            item['id'] = op_id
            item['date'] = op_date
            item['type'] = op_type
            item['amount'] = op_amount
            item['policy'] = response.meta['policy']
            yield item

            details_url = entry.xpath('td/a/@href')[0].extract()
            details_url = response.urljoin(details_url)
            if '_eventId=details' not in details_url:
                self.debug(response)
            meta = reuse_meta(response)
            meta['op_id'] = op_id
            meta['op_type'] = op_type
            meta['askedfor'] = details_url
            with open('/tmp/requested.txt', 'a') as f:
                f.write(details_url)
                f.write('\n')
            yield scrapy.Request(details_url,
                                 callback=self.on_history_details,
                                 meta=meta,
                                 dont_filter=True)

    @staticmethod
    def moneyparse(money):
        return float(money.replace(',', '.').replace(' ', ''))

    def on_history_details(self, response):
        op_id = response.meta['op_id']
        op_type = response.meta['op_type']

        if "Parametry wyszukiwania" in response.body:
            with open('/tmp/failed1.txt', 'a') as f:
                f.write(str(response.meta['redirect_urls']) + '\n')
        else:
            with open('/tmp/good.txt', 'a') as f:
                f.write(str(response.meta['redirect_urls']) + '\n')
        if 'http://portal.openlife.pl/frontend/secure/accountHistory.html?_flowId=account_history-flow' in response.meta['redirect_urls']:
            with open('/tmp/failed2.txt', 'a') as f:
                f.write(str(response.meta['redirect_urls']) + '\n')


        try:
            if op_type == 'Opłata':
                entries = response.xpath("//div/div/table/tbody/tr")
                for entry in entries:
                    fields = [e.extract().strip() for e in entry.xpath('td/text()|td/nobr/text()')]
                    _, fund_name, units_amount, unit_price, _, price_date, _, money, _, _ = fields
                    item = ScrapyOpenlifeHistoryItemDetail()
                    item['op_id'] = op_id
                    item['fund_name'] = fund_name
                    item['money_transfer'] = -OpenlifeSpider.moneyparse(money)
                    item['policy'] = response.meta['policy']
                    yield item
            elif op_type == 'Wpłaty':
                entries = response.xpath("//div/div/table/tr")
                for entry in entries:
                    fields = [e.extract().strip() for e in entry.xpath('td/text()|td/nobr/text()')]
                    _, fund_name, _, _, _, _, _, money, _, _ = fields
                    item = ScrapyOpenlifeHistoryItemDetail()
                    item['op_id'] = op_id
                    item['fund_name'] = fund_name
                    item['money_transfer'] = OpenlifeSpider.moneyparse(money)
                    item['policy'] = response.meta['policy']
                    yield item
            elif op_type == 'Przeniesienie':
                entries = response.xpath("//div/div/table/tr")
                moneytransfers = defaultdict(float)
                for entry in entries:
                    fields = [e.extract().strip() for e in entry.xpath('td/text()|td/nobr/text()')]
                    fund_name, _, _, _, _, _, money, _, _ = fields
                    moneytransfers[fund_name] += OpenlifeSpider.moneyparse(money)
                for fund_name, money in moneytransfers.iteritems():
                    item = ScrapyOpenlifeHistoryItemDetail()
                    item['op_id'] = op_id
                    item['fund_name'] = fund_name
                    item['money_transfer'] = money
                    item['policy'] = response.meta['policy']
                    yield item
            else:
                pass
                # self.debug(response)
        except Exception as e:
            pass
            # meta = response.meta
            # if 'retries' not in response.meta:
            #     response.meta['retries'] = 16
            # if response.meta['retries'] == 0:
            #     pass
            #     # self.debug(response)
            # else:
            #     response.meta['retries'] -= 1
            #     yield scrapy.Request(meta['askedfor'],
            #                          callback=self.on_history_details,
            #                          meta=meta,
            #                          dont_filter=True)


    def debug(self, response=None, inspect=False, view=True):
        if response:
            if view:
                scrapy.utils.response.open_in_browser(response)
            if inspect:
                scrapy.shell.inspect_response(response, self)
        import pdb
        pdb.set_trace()


def daterange(start_date, end_date):
    from datetime import timedelta
    for n in range(int((end_date - start_date).days)):
        day = start_date + timedelta(n)
        if day.weekday() < 5:
            yield day


def reuse_meta(response):
    return {key: response.meta[key] for key in ['policy', 'cookiejar', 'date_from']}
