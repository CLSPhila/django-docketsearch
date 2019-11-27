from __future__ import annotations
import requests
import lxml.html
import re
import time
from typing import List, Optional 
from datetime import date
import logging

requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'
logger = logging.getLogger(__name__)



class UJSSearch:

    def get_nonce(self, resp: requests.Response) -> Optional[str]:
        match = re.search(r"captchaAnswer' \)\.value = '(?P<nonce>\-?\d+)';", resp.text)
        if match:
            return match.group('nonce')
        return None

    def get_viewstate(self, resp: requests.Response) -> Optional[str]:
        match = re.search(r"input type=\"hidden\" name=\"__VIEWSTATE\" id=\"__VIEWSTATE\" value=\"(?P<viewstate>[\-0-9a-z]+)\"", resp.text)
        if match:
            return match.group('viewstate')
        return None


    def __init__(self):
        self.sess = requests.Session()
        headers = {
            'User-Agent': 'EG Testing',
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Host': 'ujsportal.pacourts.us',
        }
        self.sess.headers.update(headers)



    def search_name(self, first_name: str, last_name: str, dob: Optional[date] = None) -> dict:
        raise NotImplementedError

    def search_docket_number(self, docket_number: str) -> dict:
        raise NotImplementedError





