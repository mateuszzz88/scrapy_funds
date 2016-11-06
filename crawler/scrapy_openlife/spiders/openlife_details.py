# -*- coding: utf-8 -*-
from collections import defaultdict
from openlife import *
from pprint import pprint as pp

from crawler.scrapy_openlife.items import *
import scrapy
PATT_DATE = re.compile(r'\d\d\d\d-\d\d-\d\d')


class OpenlifeDetailsSpider(OpenlifeSpider):
    name = "openlife_details"
    allowed_domains = ["openlife.pl"]
    start_urls = (
        'https://portal.openlife.pl/frontend/login.html',
    )
    needed_details = defaultdict(set)

    def do_policy(self, response):
        meta = reuse_meta(response)
        yield scrapy.Request('https://portal.openlife.pl/frontend/secure/accountHistory.html',
                             callback=self.on_account_history,
                             meta=meta,
                             dont_filter=True)

    @staticmethod
    def optype_translate(optype):
        dct = {u'Opłata' : 'charge',
               u'Wpłaty' : 'payment',
               u'Przeniesienie' : 'transfer'}
        return dct[optype]

    def pop_details(self, response):
        needed_set = self.needed_details[response.meta['policy']]
        if len(needed_set) == 0:
            return None
        op_id, op_type = needed_set.pop()
        op_type = self.optype_translate(op_type)
        url = response.url.split('&', 1)[0]
        details_url = "%s&_eventId=details&idHistory=%s&historyType=%s" % (url, op_id, op_type)
        meta = reuse_meta(response)
        meta['op_type'] = op_type
        meta['op_id'] = op_id
        return scrapy.Request(details_url,
                              callback=self.on_history_details,
                              meta=meta,
                              dont_filter=True)


    def on_account_history(self, response):
        policy = response.meta['policy']
        # find operations with missing details (per policy)
        entries = list(PolicyOperation.objects.filter(policyoperationdetail__isnull=True, policy=response.meta['policy']))

        for entry in entries:
            op_id = entry.operation_id
            op_type = entry.operation_type
            self.needed_details[policy].add((op_id, op_type))
        concurrents = 5
        for _ in xrange(concurrents):
            yield self.pop_details(response)

    def renew_token(self, response):
        yield self.pop_details(response)

    def empty_item(self, response, op_id):
        money = response.xpath('//ul[@class="list"]/li/div/text()')[4].extract().strip()
        item = ScrapyOpenlifeHistoryItemDetail()
        item['op_id'] = op_id
        item['fund_name'] = "(none)"
        item['money_transfer'] = OpenlifeSpider.moneyparse(money)
        item['policy'] = response.meta['policy']
        return item

    def on_history_details(self, response):
        op_id = response.meta['op_id']
        op_type = response.meta['op_type']
        # scrapy.utils.response.open_in_browser(response)

        if "Parametry wyszukiwania" in response.body or "Błąd bezpieczeństwa" in response.body:
            # retry with new _flowExecutionKey
            suffix = response.meta['redirect_urls'][0].split('&', 1)[1]
            url = response.url + '&' + suffix
            meta = reuse_meta(response, ['op_id', 'op_type'])
            yield scrapy.Request(url,
                                 callback=self.on_history_details,
                                 meta=meta,
                                 dont_filter=True)
            return

        OPLATA, WPLATA, PRZENIESIENIE = 'charge', 'payment', 'transfer'
        if op_type == OPLATA:
            entries = response.xpath("//div/div/table/tbody/tr")

            for entry in entries:
                fields = [e.extract().strip() for e in entry.xpath('td/text()|td/nobr/text()')]
                if len(fields) == 9:
                    pass
                _, fund_name, units_amount, unit_price, _, price_date, _, money, _, _ = fields
                item = ScrapyOpenlifeHistoryItemDetail()
                item['op_id'] = op_id
                item['fund_name'] = fund_name
                item['money_transfer'] = -OpenlifeSpider.moneyparse(money)
                item['policy'] = response.meta['policy']
                yield item
            if not entries:
                yield self.empty_item(response, op_id)

        elif op_type == WPLATA:
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
            if not entries:
                yield self.empty_item(response, op_id)
        elif op_type == PRZENIESIENIE:
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
            if not entries:
                yield self.empty_item(response, op_id)
        else:
            scrapy.utils.response.open_in_browser(response)

        yield scrapy.Request('https://portal.openlife.pl/frontend/secure/accountHistory.html',
                             callback=self.renew_token,
                             meta=reuse_meta(response),
                             dont_filter=True)

