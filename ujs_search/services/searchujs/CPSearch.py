from .UJSSearch import UJSSearch
from .SearchResult import SearchResult
from lxml import etree
import lxml.html
import re
import time
import logging
from typing import List, Optional
from datetime import date
import asyncio
import aiohttp
import ssl

logger = logging.getLogger(__name__)

async def fetch(session, sslctx, url):
    """
    async method to fetch a url
    """
    async with session.get(url, ssl=sslctx) as response:
        if response.status == 200:
            return await response.text()
        else:
            return await response.text() 

class CPSearch(UJSSearch):
    """
    Class for searching the Court of Common Pleas.
    """
    BASE_URL = "https://ujsportal.pacourts.us/DocketSheets/CP.aspx"

    class CONTROLS:
        # Name search Control ids
        LAST_NAME = 'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$lastNameControl'
        FIRST_NAME = 'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$firstNameControl'
        DOB = 'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$dateOfBirthControl$DateTextBox'

    def search_results_from_page(self, page: etree) -> List[dict]:
        """
        Given a parsed html page, (parsed w/ lxml.html), return a list of ujs search results.

        When search results come back, there's a div w/ id 'ctl00_ctl00_ctl00_cphMain_cphDynamicContent_cphDynamicContent_participantCriteriaControl_searchResultsGridControl_resultsPanel'
        it has tr children for each result.

        The <td>s under this <tr> have the data on the search result.
        The first td has the a <table> inside it. That table has a <tr> and a <tbody> that just contains the image for the user to hover over.
        This same td also has div with display:none. That div has its own table nested inside.
            the first  tr/td has an <a> tag with a link to the Docket.  The second tr/td has an <a> tag with a link to the Summary.
 
        """
        results_panel = page.xpath("//div[@id='ctl00_ctl00_ctl00_cphMain_cphDynamicContent_cphDynamicContent_participantCriteriaControl_searchResultsGridControl_resultsPanel']")
        if len(results_panel) == 0:
            return []
        assert len(results_panel) == 1, "Did not find one and only one results panel."
        results_panel = results_panel[0]

        # Collect the columns of the table of results.
        docket_numbers = results_panel.xpath(".//span[contains(@id, 'docketNumberLabel')]")
        captions = results_panel.xpath(".//span[contains(@id, 'shortCaptionLabel')]")
        filing_dates = results_panel.xpath(
            ".//span[contains(@id, 'filingDateLabel')]"
        )
        case_statuses = results_panel.xpath(".//span[contains(@id, 'caseStatusNameLabel')]")
        otns = results_panel.xpath(".//span[contains(@id, 'otnLabel')]")
        dobs = results_panel.xpath(".//span[contains(@id, 'DobLabel')]")

        docket_sheet_urls = results_panel.xpath(".//a[contains(@href,'CPReport.ashx?docketNumber=')]")

        summary_urls = results_panel.xpath(".//a[contains(@href,'CourtSummaryReport.ashx?docketNumber=')]")

        # check that the length of all these lists is the same, so that
        # they get zipped up properly.
        assert len(set(map(len, (
            docket_numbers, docket_sheet_urls, summary_urls,
            captions, filing_dates, case_statuses, dobs)))) == 1

        results =  [
            SearchResult(
                docket_number = dn.text,
                docket_sheet_url = ds.get("href"),
                summary_url = su.get("href"),
                caption = cp.text,
                filing_date = fd.text,
                case_status = cs.text,
                otn = otn.text,
                dob = dob.text,
            )
            for dn, ds, su, cp, fd, cs, otn, dob in zip(
                docket_numbers,
                docket_sheet_urls,
                summary_urls,
                captions,
                filing_dates,
                case_statuses,
                otns,
                dobs
            )
        ]
        return results



    def get_select_person_search_data(self, changes):
        """
        Get a dict with the keys/values for telling the site that we would like to search for a person's 
        name.
        """
        dt = {
            '__EVENTTARGET': 'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$searchTypeListControl',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATEGENERATOR': '751CF88B',
            '__SCROLLPOSITIONX': 0,
            '__SCROLLPOSITIONY': 0,
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$searchTypeListControl': 'Aopc.Cp.Views.DocketSheets.IParticipantSearchView, CPCMSApplication, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$docketNumberCriteriaControl$docketNumberControl$mddlCourt':'',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$docketNumberCriteriaControl$docketNumberControl$mtxtCounty': '',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$docketNumberCriteriaControl$docketNumberControl$mddlDocketType': '',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$docketNumberCriteriaControl$docketNumberControl$mtxtSequenceNumber': '',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$docketNumberCriteriaControl$docketNumberControl$mtxtYear': '',
        }
        dt.update(changes)
        return dt

    def get_search_form_data(self, changes):
        dt = {
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$searchTypeListControl': 'Aopc.Cp.Views.DocketSheets.IParticipantSearchView, CPCMSApplication, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null',
            self.CONTROLS.LAST_NAME: '',
            self.CONTROLS.FIRST_NAME: '',
            self.CONTROLS.DOB: '',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$dateOfBirthControl$DateTextBoxMaskExtender_ClientState': '',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$countyListControl:': '',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$docketTypeListControl': '',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$caseCategoryListControl': '',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$caseStatusListControl': '',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$dateFiledControl$beginDateChildControl$DateTextBox': '01/01/1950',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$dateFiledControl$beginDateChildControl$DateTextBoxMaskExtender_ClientState': '',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$dateFiledControl$endDateChildControl$DateTextBox': '11/25/2019',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$dateFiledControl$endDateChildControl$DateTextBoxMaskExtender_ClientState': '',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$searchCommandControl': 'Search',
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS':'',
            '__VIEWSTATEGENERATOR': '751CF88B',
            '__SCROLLPOSITIONX': 0,
            '__SCROLLPOSITIONY': 0,
            '__VIEWSTATEENCRYPTED': '',
        }
        dt.update(changes)
        return dt


    def search_name(self, first_name: str, last_name: str, dob: Optional[date] = None) -> dict:
        """
        Search CP by name. 
        """
        if dob:
            dob = dob.strftime(r"%m/%d/%Y")
        # Get the main page.
        main_page = self.sess.get(self.BASE_URL)
        assert main_page.status_code == 200, "Request for landing page failed."
        logger.info("GOT main page")
        time.sleep(1)

        nonce = self.get_nonce(main_page)
        assert nonce is not None, "couldn't find nonce on main page."

        viewstate = self.get_viewstate(main_page)
        assert viewstate is not None, "couldn't find viewstate on main page"

        # Now select the participant name search
        select_person_search_data = self.get_select_person_search_data({
            'ctl00$ctl00$ctl00$ctl07$captchaAnswer': nonce,
            '__VIEWSTATE': viewstate,
        })

        search_page = self.sess.post(self.BASE_URL, data=select_person_search_data)
        assert search_page.status_code == 200, "Request for search page failed."

        logging.info("GOT participant search page")
        # with open("participantSearch.html", "wb") as f:
        #     f.write(resp.content)
        time.sleep(1)

        nonce = self.get_nonce(search_page)
        assert nonce is not None, "couldn't find nonce on participant search page"
        
        viewstate = self.get_viewstate(search_page)
        assert viewstate is not None, "couldn't find viewstate on person search page"

        search_form_data = self.get_search_form_data({
            'ctl00$ctl00$ctl00$ctl07$captchaAnswer': nonce,
            '__VIEWSTATE': viewstate,
            self.CONTROLS.LAST_NAME: last_name,
            self.CONTROLS.FIRST_NAME: first_name,
            self.CONTROLS.DOB : dob or ""
        })
        
        # Make the search request.
        search_results_page = self.sess.post(self.BASE_URL, data=search_form_data)
        assert search_results_page.status_code == 200, "Request for search results failed."
        print("GOT search results back")

        #with open("participantSearchResults.html", "wb") as f:
        #    f.write(search_results_page.content)

        parsed_page = lxml.html.document_fromstring(search_results_page.text)
        results = self.search_results_from_page(parsed_page)

        logging.info(f"Found {len(results)} results")

        return results


    def get_docket_search_post_data(self, court, county, dkttype, docket_num, year, nonce, viewstate):
        """
        Build a dict with the data to POST to search for a specific docket.

        Args:
            court: CP or MC
            county (str): like 43, 21. Indicates a county in PA.
            dkttype (str): CR, MD, and  so on.
            docket_num (str): A string of 7 digits, like 0123456
            year (str): Four digit year.
            nonce (str): nonce for the search page.
            viewstate (str): asp.net viewstate for the search page.
        """
        SEARCH_TYPE = 'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$searchTypeListControl'
        COURT = 'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$docketNumberCriteriaControl$docketNumberControl$mddlCourt'
        COUNTY = 'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$docketNumberCriteriaControl$docketNumberControl$mtxtCounty'
        DKT_TYPE = 'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$docketNumberCriteriaControl$docketNumberControl$mddlDocketType'
        DKT_NUM = 'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$docketNumberCriteriaControl$docketNumberControl$mtxtSequenceNumber'
        YEAR = 'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$docketNumberCriteriaControl$docketNumberControl$mtxtYear'
        SEARCH_CONTROL = 'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$docketNumberCriteriaControl$searchCommandControl'
        NONCE = 'ctl00$ctl00$ctl00$ctl07$captchaAnswer'

        return {
            "_VIEWSTATE": viewstate,
            "_VIEWSTATEGENERATOR": "751CF88B",
            '__SCROLLPOSITIONX': 0,
            '__SCROLLPOSITIONY': 0,
            COURT: court,
            COUNTY: county,
            DKT_TYPE: dkttype,
            DKT_NUM: docket_num,
            YEAR: year,
            SEARCH_CONTROL: 'Search',
            NONCE: nonce,
        }



    async def search_docket_number(self, docket_number: str) -> dict:
        """
        async coroutine to search the court of common pleas for a single docket number. 


        TODO the session should be created at a higher level and passed down to this method.
        """
        sslcontext = ssl.create_default_context()
        sslcontext.set_ciphers("HIGH:!DH:!aNULL")
        headers = self.__headers__
        async with aiohttp.ClientSession(headers=headers) as session:
            search_page = await fetch(session, sslcontext, self.BASE_URL)

            nonce = self.get_nonce(search_page)
            assert nonce is not None, "couldn't find nonce on participant search page"

            viewstate = self.get_viewstate(search_page)
            assert viewstate is not None, "couldn't find viewstate on person search page"

            search_data = self.get_docket_search_post_data(
                **self.parse_docket_number(docket_number),
                nonce=nonce,
                viewstate=viewstate
            )

            search_results = await post(session, sslcontext, self.BASE_URL, self.)

            breakpoint()
            return []
