from .UJSSearch import UJSSearch
from .SearchResult import SearchResult
from lxml import etree
import lxml.html
import re
import time
import logging
from typing import List, Optional, Dict, Tuple
from datetime import date
import asyncio
import aiohttp
import ssl
from collections import namedtuple

logger = logging.getLogger(__name__)

DocketNumber = namedtuple('DocketNumber', 'court county dkt_type sequence year')

 

class CPSearch(UJSSearch):
    """
    Class for searching the Court of Common Pleas.
    """
    PREFIX_URL = "https://ujsportal.pacourts.us/DocketSheets/"
    BASE_URL = PREFIX_URL + "CP.aspx"

    DOCKET_NUMBER_REGEX = r"^(?P<court>CP|MC)-(?P<county>[0-9]{2})-(?P<dkt_type>CR|MD|SA|SU)-(?P<sequence>[0-9]{7})-(?P<year>[0-9]{4})"


    class CONTROLS:
        # Name search Control ids
        LAST_NAME = 'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$lastNameControl'
        FIRST_NAME = 'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$firstNameControl'
        DOB = 'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$dateOfBirthControl$DateTextBox'

    def search_results_from_page(self, page: str) -> List[dict]:
        """
        Given a parsed html page, (parsed w/ lxml.html), return a list of ujs search results.

        When search results come back, there's a div w/ id 'ctl00_ctl00_ctl00_cphMain_cphDynamicContent_cphDynamicContent_participantCriteriaControl_searchResultsGridControl_resultsPanel'
        it has tr children for each result.

        The <td>s under this <tr> have the data on the search result.
        The first td has the a <table> inside it. That table has a <tr> and a <tbody> that just contains the image for the user to hover over.
        This same td also has div with display:none. That div has its own table nested inside.
            the first  tr/td has an <a> tag with a link to the Docket.  The second tr/td has an <a> tag with a link to the Summary.
 
        """
        page = lxml.html.document_fromstring(page.strip())

        results_panel = page.xpath("//div[contains(@id, 'resultsPanel')]")
        #page.xpath("//div[@id='ctl00_ctl00_ctl00_cphMain_cphDynamicContent_cphDynamicContent_participantCriteriaControl_searchResultsGridControl_resultsPanel']")
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
                docket_sheet_url = self.PREFIX_URL + ds.get("href") if dn.text in ds.get("href") else "Docket URL not found",
                summary_url = self.PREFIX_URL + su.get("href") if dn.text in su.get("href") else "Summary URl not found",
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
        
        This is for the intermediary step of simply getting the page from which we can search for a name.
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

    def get_name_search_form_data(self, changes):
        """
        Get the data to POST to complete a search by name for a person.
        """
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
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$dateFiledControl$endDateChildControl$DateTextBox': self.today,
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

    def get_search_pager_form_data(self, namesearch_data: dict, target: str, viewstate: str, nonce: str):
        """
        Get the data to POST to get second, third, and so on pages of search results. 

        This takes the data posted for the original search and slightly modifies it, 
        in order to get the correct page for the same search.

        Args:
            name_search_data (dict): The dict that was POSTed to get the first search results. 
            target (str): the id of the target page to get. 
        """
        namesearch_data.pop("ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphDynamicContent$participantCriteriaControl$searchCommandControl")
        namesearch_data.update({
            '__EVENTTARGET': target,
            '__VIEWSTATE': viewstate,
            'ctl00$ctl00$ctl00$ctl07$captchaAnswer': nonce,
        })
        return namesearch_data

    def find_additional_page_links(self, page: str) -> List[str]:
        """ Given the text of a search results page, find any links to additional results pages.

        A UJS search results page might have paginated results. Give this function the text of the first 
        page, and it will find strings identifying pages 2 through 5. 

        It will either return a list of those strings, or an empty list, if no additional pages are 
        found. 

        Another function will figure out how to use those strings in POST requests to actually 
        fetch the resources those strings point to.

        N.B. This depends on the User-Agent being something non-standard. For example, a Chrome user-agent will return a page that this function
        won't match. 
        """
        # TODO There are now two functions that parse the CP search results to an lxml etree. Not DRY!
        page = lxml.html.document_fromstring(page.strip())
        pagination_span_id = "ctl00_ctl00_ctl00_cphMain_cphDynamicContent_cphDynamicContent_participantCriteriaControl_searchResultsGridControl_casePager"
        # collect the <a> elements that link to the results pages 2-5.
        xpath_query=f"//span[@id='{pagination_span_id}']/div/a[u[text()='2' or text()='3' or text()='4' or text()='5']]"

        links = page.xpath(xpath_query)
        links = [l.get('href') for l in links]
        # The links trigger js postbacks, but all we want (all we can use) is an id for building our own
        # post request.
        patt = re.compile(
            "^javascript:__doPostBack\('(?P<link>.*)',''\)$"
        )
        matches = [patt.match(l) for l in links]
        just_the_important_parts = [m.group('link') for m in matches if m is not None]
        return just_the_important_parts


    async def fetch_cases_from_additional_page(
        self, namesearch_data: dict, link: str, viewstate: str, nonce: str, 
        session, sslcontext) -> Tuple[List[dict], str, str]:
        """ Given a string identifying a page-2-or-more page of UJS Search results, 
        fetch the page this string refers to, and parse the cases on that page. 

        Use this link string to build a POST request that fetches a page of search results. 

        Args:
            link (str): This is a string identifying a page of up to 10 search results for a name.

        """
        logger.info(f"Fetching page: {link[-12:-6]}")

        # get the dict for POSTing
        data = self.get_search_pager_form_data(
            namesearch_data=namesearch_data, target=link, viewstate=viewstate, nonce=nonce)
        # do the POST
        next_page =  await self.post(session, sslcontext, self.BASE_URL, data)
        if next_page == "":
            logging.error(f"Fetching {link} failed.")
            return []


        # parse the result pages.
        results = self.search_results_from_page(next_page)
        logger.info(f"Fetched page: {link[-12:-6]}")
        logger.info(f"  And found {len(results)} new results")
        return results


    async def search_name(self, first_name: str, last_name: str, dob: Optional[date] = None) -> Tuple[List, List]:
        """
        Search CP by name. 

        Args:
            first_name (str): Person's first name
            last_name (str): Last name
            dob (Optional[date]): Person's date of birth, or None.

        Returns:
            A tuple with - 
            List of search results, and 
            List of errors or empty list
        """
        sslcontext = ssl.create_default_context()
        sslcontext.set_ciphers("HIGH:!DH:!aNULL")
        headers = self.__headers__
        if dob:
            dob = dob.strftime(r"%m/%d/%Y")
        # Get the main page.
        async with aiohttp.ClientSession(headers=headers) as session:
            main_page = await self.fetch(session, sslcontext, self.BASE_URL)
            assert main_page != "", "Request for landing page failed."
            logger.info("GOT main page")

            nonce = self.get_nonce(main_page)
            assert nonce is not None, "couldn't find nonce on main page."

            viewstate = self.get_viewstate(main_page)
            assert viewstate is not None, "couldn't find viewstate on main page"

            # Now select the participant name search
            select_person_search_data = self.get_select_person_search_data({
                'ctl00$ctl00$ctl00$ctl07$captchaAnswer': nonce,
                '__VIEWSTATE': viewstate,
            })

            search_page = await self.post(session, sslcontext, self.BASE_URL, select_person_search_data)
            assert search_page != "", "Request for search page failed."

            logging.info("GOT participant search page")
            # with open("participantSearch.html", "wb") as f:
            #     f.write(resp.content)

            nonce = self.get_nonce(search_page)
            assert nonce is not None, "couldn't find nonce on participant search page"
            
            viewstate = self.get_viewstate(search_page)
            assert viewstate is not None, "couldn't find viewstate on person search page"

            search_form_data = self.get_name_search_form_data({
                'ctl00$ctl00$ctl00$ctl07$captchaAnswer': nonce,
                '__VIEWSTATE': viewstate,
                self.CONTROLS.LAST_NAME: last_name,
                self.CONTROLS.FIRST_NAME: first_name,
                self.CONTROLS.DOB : dob or ""
            })
            
            # Make the search request.
            first_search_results_page = await self.post(session, sslcontext, self.BASE_URL, search_form_data)
            assert first_search_results_page != "", "Request for search results failed."
            nonce = self.get_nonce(first_search_results_page)
            assert nonce is not None, "couldn't find nonce on participant search page"
            
            viewstate = self.get_viewstate(first_search_results_page)
            assert viewstate is not None, "couldn't find viewstate on person search page"

            results = self.search_results_from_page(first_search_results_page)

            # If there are multiple pages of search results, there will be links at the bottom
            # of the search table. 
            # If there are any such links, fetch the pages they link to.

            additional_page_links = self.find_additional_page_links(first_search_results_page)
            for link in additional_page_links:
                if self.keep_going() is False:
                    self.errors.append(f"too many results to process in {self.timelimit} seconds")
                    break
                additional_results = await self.fetch_cases_from_additional_page(
                    namesearch_data=search_form_data.copy(), link=link, viewstate=viewstate, nonce=nonce, 
                    session=session, sslcontext=sslcontext)
                results.extend(additional_results)

            logging.info(f"Found {len(results)} results")

            return results, self.errors 

    def parse_docket_number(self, full_dn: str) -> DocketNumber:
        """
        Parse a CP Docket number into its component parts.

        Args:
            full_dn (str): A docket number, like CP-43-CR-0123456-2000

        Returns:
            A DocketNumber namedtuple of the components of the full docket number.
        """
        patt = re.compile(self.DOCKET_NUMBER_REGEX, re.IGNORECASE)
        matches = patt.match(full_dn)
        if not matches:
            raise ValueError(f"{full_dn} was not a correctly formatted docket number.")
        return DocketNumber(
            court = matches.group('court'),
            county = matches.group('county'),
            dkt_type = matches.group('dkt_type'),
            sequence = matches.group('sequence'),
            year = matches.group('year'),
        )

    def get_docket_search_post_data(self, court, county, dkt_type, sequence, year, nonce, viewstate):
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
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": "751CF88B",
            '__SCROLLPOSITIONX': 0,
            '__SCROLLPOSITIONY': 0,
            COURT: court,
            COUNTY: county,
            DKT_TYPE: dkt_type,
            DKT_NUM: sequence,
            YEAR: year,
            SEARCH_CONTROL: 'Search',
            NONCE: nonce,
        }

    async def search_docket_number(self, docket_number: str) -> dict:
        """
        async coroutine to search the court of common pleas for a single docket number. 


        TODO the session should be created at a higher level and passed down to this method.
        """
        docket_number = docket_number.upper()
        sslcontext = ssl.create_default_context()
        sslcontext.set_ciphers("HIGH:!DH:!aNULL")
        headers = self.__headers__
        async with aiohttp.ClientSession(headers=headers) as session:
            search_page = await self.fetch(session, sslcontext, self.BASE_URL)

            nonce = self.get_nonce(search_page)
            assert nonce is not None, "couldn't find nonce on participant search page"

            viewstate = self.get_viewstate(search_page)
            assert viewstate is not None, "couldn't find viewstate on person search page"

            search_data = self.get_docket_search_post_data(
                **self.parse_docket_number(docket_number)._asdict(),
                nonce=nonce,
                viewstate=viewstate
            )

            search_results_page = await self.post(session, sslcontext, self.BASE_URL, search_data) 
            if search_results_page == "":
                return [{"error": "Searching failed."}]
            
            search_results = self.search_results_from_page(search_results_page)
            return search_results
