from __future__ import annotations
import requests
import lxml.html
import re
import time
from typing import List, Optional, Union, Tuple
from datetime import date
import logging
import aiohttp
from .SearchResult import SearchResult


# requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += "HIGH:!DH:!aNULL"
logger = logging.getLogger(__name__)


SITE_ROOT = "https://ujsportal.pacourts.us"


def parse_row_column(row: "etree", position: int) -> str:
    """
    Get the value of a column in an html table row.
    """
    path = f"./td[position()='{position}']"
    result = "".join([res.text for res in row.xpath(path) if res.text is not None])
    return result


def parse_link_column(row: "etree") -> Tuple[str, str]:
    """
    Extract the urls to the docket and summary sheet of a
    search result.
    """
    path = "./td[position()='19']//a"
    results = row.xpath(path)

    links = set([res.get("href", "") for res in results])

    if len(links) != 2:
        return "", ""
    return tuple(links)


def parse_row(row: "etree") -> SearchResult:
    """
    Read a single row of a docket search result table.

    """
    urls = parse_link_column(row)

    res = SearchResult(
        docket_number=parse_row_column(row, 3),
        court=parse_row_column(row, 4),
        caption=parse_row_column(row, 5),
        case_status=parse_row_column(row, 6),
        filing_date=parse_row_column(row, 7),
        participants=parse_row_column(row, 8),
        dob=parse_row_column(row, 9),
        county=parse_row_column(row, 10),
        otn=parse_row_column(row, 12),
        docket_sheet_url=SITE_ROOT + urls[0],
        summary_url=SITE_ROOT + urls[1],
    )
    return res


class UJSSearch:
    """
    Class for managing sessions and requests for using the UJS portal.
    """

    def get_request_verification_token(self, text: str) -> str:
        """
        Find the request verification token in a text
        """
        match = re.search(
            r"input name=\"__RequestVerificationToken\" type=\"hidden\" value=\"(?P<token>[\-0-9a-zA-Z_]+)\"",
            text,
        )
        if match:
            return match.group("token")
        return ""

    async def fetch(self, url):
        """
        async method to fetch a url
        """
        async with self.sess.get(url) as response:
            if response.status == 200:
                return (await response.text(), [])
            else:
                err = f"GET {url} failed with {response.status}"
                return "", [err]

    async def post(self, url, data, additional_headers=None):
        """
        async method to post data to a url.
        """
        if additional_headers:
            headers_to_send = self.__headers__.copy()
            headers_to_send.update(additional_headers)
            # headers_to_send.pop("Upgrade-Insecure-Requests")
        else:
            headers_to_send = self.__headers__
        async with self.sess.post(url, data=data, headers=headers_to_send) as response:
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

    def parse_results_from_page(
        self, page: str
    ) -> Tuple[List[SearchResult], List[str]]:
        """
        Extract a list of docket search results from the search results table.
        """
        page = lxml.html.document_fromstring(page.strip())
        results_table = page.xpath("//table[@id='caseSearchResultGrid']/tbody/tr")
        if len(results_table) == 0:
            return [], ["Could not find table of search results"]
        search_results = [
            item
            for item in [parse_row(row) for row in results_table]
            if item is not None
        ]
        return search_results, []

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

    def __init__(self, session):
        """
        Create the UJS Search helper.

        Args:
            session: a session object. Create with a context manager.
        """
        self.today = date.today().strftime(r"%m/%d/%Y")
        self.sess = session
        # self.sess = requests.Session()  # deprecated. need to switch to aio session.
