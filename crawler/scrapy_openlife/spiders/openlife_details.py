# -*- coding: utf-8 -*-
import datetime
import re
from report.models import Policy, PolicyOperation, PolicyOperationDetail
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
    # custom_settings = {
    #     'SOME_SETTING': 'some value',
    # }
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
               u'Wpłata' : 'payment',
               u'Przeniesienie' : 'transfer'}
        return dct[optype]

    def pop_details(self, response):
        with open('/tmp/history.txt', 'a') as fil:
            fil.write("POP ")
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
        with open('/tmp/history.txt', 'a') as fil:
            fil.write("POP tries %s (%s)\n" % (details_url, str(meta)))
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
        url = response.url
        concurrents = 5
        for _ in xrange(concurrents):
            yield self.pop_details(response)

        #     operation = PolicyOperation.objects.filter(policy=response.meta['policy'], operation_id=op_id)
        #     if not operation:
        #         op_type = op_type.encode('utf-8')
        #         op_amount = float(op_amount.replace(',', '.').replace(u'\xa0', ''))
        #         item = ScrapyOpenlifeHistoryItem()
        #         item['id'] = op_id
        #         item['date'] = op_date
        #         item['type'] = op_type
        #         item['amount'] = op_amount
        #         item['policy'] = response.meta['policy']
        #         yield item
        #     else:
        #         # operation already in db, if details are also then don't download them
        #         operation = operation[0]
        #         has_details = operation.policyoperationdetail_set.count() > 0
        #         if has_details:
        #             continue  # do not download details
        #
        #     details_url = entry.xpath('td/a/@href')[0].extract()
        #     details_url = response.urljoin(details_url)
        #     if '_eventId=details' not in details_url:
        #         self.debug(response)
        #     # meta = reuse_meta(response)
        #     meta = dict()
        #     meta['policy'] = response.meta['policy']
        #     meta['cookiejar'] = response.meta['cookiejar']
        #     meta['op_id'] = op_id
        #     meta['op_type'] = op_type #.encode('utf-8')
        #     meta['askedfor'] = details_url
        #     # with open('/tmp/requested.txt', 'a') as f:
        #     #     f.write(details_url)
        #     #     f.write('\n')
        #     # yield scrapy.Request(details_url,
        #     #                      callback=self.on_history_details,
        #     #                      meta=meta,
        #     #                      dont_filter=True)
        #     self.needed_details.add((details_url.split('&', 1)[1], frozenset(meta.items())))
        # # self.debug(response)
        # url = response.url
        # yield self.pop_details(url)
        # yield self.pop_details(url)

    def on_history_details(self, response):
        op_id = response.meta['op_id']
        op_type = response.meta['op_type']

        if "Parametry wyszukiwania" in response.body or "Błąd bezpieczeństwa" in response.body:
            # retry with new _flowExecutionKey
            suffix = response.meta['redirect_urls'][0].split('&', 1)[1]
            url = response.url + '&' + suffix
            meta = reuse_meta(response, ['op_id', 'op_type'])
            yield scrapy.Request(url,
                                 callback=self.on_history_details,
                                 meta=meta,
                                 dont_filter=True)

            with open('/tmp/failed1.txt', 'a') as f:
                f.write(str(response.meta['redirect_urls']) + ' -->  ' + url + '\n')
            return
        else:
            with open('/tmp/good.txt', 'a') as f:
                f.write(str(response.meta['redirect_urls']) + '\n')

        # OPLATA, WPLATA, PRZENIESIENIE = u'Opłata', u'Wpłaty', u'Przeniesienie'
        OPLATA, WPLATA, PRZENIESIENIE = 'charge', 'payment', 'transfer'
        if op_type == OPLATA:
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
        else:
            pass
            # self.debug(response)
        # yield self.pop_details(response)

