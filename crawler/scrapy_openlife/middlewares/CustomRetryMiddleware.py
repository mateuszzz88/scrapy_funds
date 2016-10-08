from scrapy.downloadermiddlewares.retry import *
from scrapy.downloadermiddlewares.redirect import *
from pprint import pprint as pp
import pdb
from crawler.scrapy_openlife.spiders.openlife import *
from urlparse import urljoin


class CustomRetryMiddleware(RetryMiddleware):

    def __init__(self, settings):
        super(CustomRetryMiddleware, self).__init__(settings)

    def process_response(self, request, response, spider):
        # print "in process_response"
        # pdb.set_trace()
        if request.callback:
            try:
                if request.callback.im_func == OpenlifeSpider.on_history_details.im_func:
                    if 'http://portal.openlife.pl/frontend/secure/accountHistory.html?_flowId=account_history-flow' in response.meta.get('redirect_urls', []):
                        pdb.set_trace()
                if request.callback.im_func == OpenlifeSpider.on_account_history.im_func:
                    if 'http://portal.openlife.pl/frontend/secure/accountHistory.html?_flowId=account_history-flow' in response.meta.get('redirect_urls', []):
                        pdb.set_trace()
            except Exception as e:
                with open('/tmp/failed_nometa.txt', 'a') as f:
                    f.write("%s  -  %s\n" % (request.url, response.url))
        if request.meta.get('dont_retry', False):
            return response
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        return response


class CustomRedirectMiddleware(RedirectMiddleware):
    # def __init__(self, settings):
    #     if not settings.getbool(self.enabled_setting):
    #         raise NotConfigured
    #
    #     self.max_redirect_times = settings.getint('REDIRECT_MAX_TIMES')
    #     self.priority_adjust = settings.getint('REDIRECT_PRIORITY_ADJUST')

    def process_response(self, request, response, spider):
        BAD = 'http://portal.openlife.pl/frontend/secure/accountHistory.html?_flowId=account_history-flow'
        prev = request.url
        if request.meta.get('dont_redirect', False):
            return response

        if request.method == 'HEAD':
            pdb.set_trace()
            if response.status in [301, 302, 303, 307] and 'Location' in response.headers:
                redirected_url = urljoin(request.url, response.headers['location'])
                redirected = request.replace(url=redirected_url)
                return self._redirect(redirected, request, spider, response.status)
            else:
                return response

        if response.status in [302, 303] and 'Location' in response.headers:
            redirected_url = urljoin(request.url, response.headers['location'])
            if redirected_url == BAD:
                redirected_url = prev
                # pdb.set_trace()
                with open('/tmp/reredirected.txt', 'a') as f:
                    f.write(str(redirected_url) + '\n')
            redirected = self._redirect_request_using_get(request, redirected_url)
            return self._redirect(redirected, request, spider, response.status)

        if response.status in [301, 307] and 'Location' in response.headers:
            redirected_url = urljoin(request.url, response.headers['location'])
            redirected = request.replace(url=redirected_url)
            return self._redirect(redirected, request, spider, response.status)

        return response
