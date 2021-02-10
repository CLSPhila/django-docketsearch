from __future__ import annotations
import requests
import lxml.html
import re
import time
from typing import List, Optional, Union
from datetime import date
import logging
import aiohttp

requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += "HIGH:!DH:!aNULL"
logger = logging.getLogger(__name__)
logger.setLevel = logging.WARNING


class UJSSearch:
    """
    Class for managing sessions and requests for using the UJS portal.
    """

    def get_nonce(self, resp: Union[requests.Response, str]) -> Optional[str]:
        try:
            txt = resp.text
        except:
            txt = resp
        match = re.search(r"captchaAnswer' \)\.value = '(?P<nonce>\-?\d+)';", txt)
        if match:
            return match.group("nonce")
        return None

    def get_viewstate(self, resp: Union[requests.Response, str]) -> Optional[str]:
        try:
            txt = resp.text
        except:
            txt = resp
        match = re.search(
            r"input type=\"hidden\" name=\"__VIEWSTATE\" id=\"__VIEWSTATE\" value=\"(?P<viewstate>[\-0-9a-z]+)\"",
            txt,
        )
        if match:
            return match.group("viewstate")
        return None

    async def fetch(self, session, sslctx, url):
        """
        async method to fetch a url
        """
        async with session.get(url, ssl=sslctx) as response:
            if response.status == 200:
                return (await response.text(), [])
            else:
                err = f"GET {url} failed with {response.status}"
                return "", [err]

    async def post(self, session, sslctx, url, data, additional_headers=None):
        """
        async method to post data to a url.
        """
        if additional_headers:
            headers_to_send = self.__headers__.copy()
            headers_to_send.update(additional_headers)
            # headers_to_send.pop("Upgrade-Insecure-Requests")
        else:
            headers_to_send = self.__headers__
        async with session.post(
            url, ssl=sslctx, data=data, headers=headers_to_send
        ) as response:
            if response.status == 200:
                return (await response.text(), [])
            else:
                # getting the text from the response seems to be neccessary to avoid a bug in openssl (or somewhere else)
                # with ssl connections closing too soon.
                #
                # use response.request_info to see what was actually requested.
                txt = await response.text()
                err = f"POST {url} failed with status {response.status}"
                return "", [err]

    __headers__ = {
        "User-Agent": "CleanSlateScreening",
        #'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36',
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Host": "ujsportal.pacourts.us",
    }

    def __init__(self):
        self.today = date.today().strftime(r"%m/%d/%Y")
        self.sess = aiohttp.ClientSession()
        # self.sess = requests.Session()  # deprecated. need to switch to aio session.
        self.sess.headers.update(self.__headers__)

    def search_name(
        self, first_name: str, last_name: str, dob: Optional[date] = None
    ) -> dict:
        raise NotImplementedError

    def search_docket_number(self, docket_number: str) -> dict:
        raise NotImplementedError
