# -*- coding: utf-8 -*-
import datetime
import re
from report.models import DataPoint, InvestmentFund, Policy, PolicyOperation
from pprint import pprint as pp

from crawler.scrapy_openlife.items import *
PATT_DATE = re.compile(r'\d\d\d\d-\d\d-\d\d')

OVERRIDE_POLICY = None  # 'Aneta'
OVERRIDE_DATE_FROM = None  # '2012-05-01'
OVERRIDE_DATE_TO = None  # '2013-10-16'



class OpenlifeSpider(scrapy.Spider):
    name = "openlife"
    allowed_domains = ["openlife.pl"]
    start_urls = (
        'https://portal.openlife.pl/frontend/login.html',
    )

    def parse(self, response):
        policys = Policy.objects.filter(company='openlife')
        if OVERRIDE_POLICY:
            policys = [Policy.objects.get(name=OVERRIDE_POLICY)]
        for policy in policys:
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
        max_date = datetime.date.today()  # TODO this should be read from page/meta
        if OVERRIDE_DATE_FROM:
            min_date = datetime.datetime.strptime(OVERRIDE_DATE_FROM, "%Y-%m-%d").date()
        if OVERRIDE_DATE_TO:
            max_date = datetime.datetime.strptime(OVERRIDE_DATE_TO, "%Y-%m-%d").date()
        meta = reuse_meta(response)
        meta['wanted_page'] = 1
        yield scrapy.Request('https://portal.openlife.pl/frontend/secure/accountHistory.html',
                             callback=self.on_account_history,
                             meta=meta,
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

            fund = InvestmentFund.objects.filter(name=name, policy=response.meta['policy']).first()
            if fund:
                item = DataPoint.objects.filter(price_date=pricedate, fund=fund).first()
                if item:
                    continue
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
        next_page = response.xpath("//a[@id='linkNextPage']/@href").extract()
        curr_page = int(response.xpath('//a[@class="activePage"]/text()').extract()[0].strip())
        expected_page = response.meta['wanted_page']

        if curr_page != expected_page:
            # retry with new _flowExecutionKey
            meta = reuse_meta(response, ['wanted_page'])
            url = response.url + '&_eventId=gotoPage&page=' + str(expected_page)
            yield scrapy.Request(url,
                                 callback=self.on_account_history,
                                 meta=meta,
                                 dont_filter=True)
            return

        if next_page:
            next_page = next_page[0].strip()
            next_page = response.urljoin(next_page)
            meta = reuse_meta(response)
            meta['wanted_page'] = curr_page + 1

            yield scrapy.Request(next_page,
                                 callback=self.on_account_history,
                                 meta=meta,
                                 dont_filter=True)

        entries = response.xpath("//div[@class='boxContent_lvl2']/div/table/tbody/tr")
        for entry in entries:
            fields = [e.extract().strip() for e in entry.xpath('td/text()')]
            _, visible_op_id, op_date, op_type, op_amount, _, _, details, _ = fields
            m = re.search(r'idHistory=(\d+)&', entry.xpath('td/a/@href')[0].extract())
            op_id = int(m.group(1))

            operation = PolicyOperation.objects.filter(policy=response.meta['policy'], operation_id=op_id)
            if not operation:
                op_type = op_type.encode('utf-8')
                op_amount = float(op_amount.replace(',', '.').replace(u'\xa0', ''))
                if op_type.decode('utf-8') in [PolicyOperation.CHARGE, PolicyOperation.WITHDRAW]:
                    op_amount = -op_amount
                item = ScrapyOpenlifeHistoryItem()
                item['id'] = op_id
                item['date'] = op_date
                item['type'] = op_type
                item['amount'] = op_amount
                item['policy'] = response.meta['policy']
                yield item

    @staticmethod
    def moneyparse(money):
        ret = float(money.replace(',', '.').replace(' ', '').replace(u'\xa0','').replace('PLN', ''))
        return ret


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
        day = end_date - timedelta(n)
        if day.weekday() < 5:
            yield day


def reuse_meta(response, additional_keys=None):
    keys = ['policy', 'cookiejar', 'date_from'] + (additional_keys or [])
    return {key: response.meta[key] for key in keys if key in response.meta}
