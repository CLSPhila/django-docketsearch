from .UJSSearch import UJSSearch
from .SearchResult import SearchResult
from lxml import etree
import lxml.html
import re
import ssl
import aiohttp
import time
import logging
from typing import List, Optional, Tuple
from collections import namedtuple
from datetime import date
import csv
import ujs_search
import os

logger = logging.getLogger(__name__)
DocketNumber = namedtuple('DocketNumber', 'court county office dkt_type sequence year')



class MDJSearch(UJSSearch):
    PREFIX_URL = "https://ujsportal.pacourts.us/DocketSheets/"
    BASE_URL = PREFIX_URL + "MDJ.aspx"
    DOCKET_NUMBER_REGEX = r"^(?P<court>MJ)-(?P<county>[0-9]{2})(?P<office>[0-9]{3})-(?P<dkt_type>CR|CV|LT|NT|TR)-(?P<sequence>[0-9]{7})-(?P<year>[0-9]{4})"

    class CONTROLS:
        """
        Constants identifying form fields that are submitted to UJS.
        """
        # name
        SEARCH_TYPE = "ctl00$ctl00$ctl00$cphMain$cphDynamicContent$ddlSearchType"
        NONCE = "ctl00$ctl00$ctl00$ctl07$captchaAnswer"
        VIEWSTATE = "__VIEWSTATE"
        COUNTY = "ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$ddlCounty"
        LAST_NAME = "ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsParticipantName$txtLastName"
        FIRST_NAME = "ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsParticipantName$txtFirstName"
        DOB = "ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsParticipantName$dpDOB$DateTextBox"


    def search_results_from_table(self, results_panel: etree.Element) -> List:
        """
        Given a table of case search results from the MDJ portal, parse the cases into a list of dicts.


        """
        docket_numbers = results_panel.xpath(
        ".//td[2]")
        captions = results_panel.xpath(
            ".//td[4]/span")
        filing_dates = results_panel.xpath(
            ".//td[5]"
        )
        case_statuses = results_panel.xpath(
            ".//td[7]/span")
        otns = results_panel.xpath(
            ".//td[9]/span")
        dobs = results_panel.xpath(
            ".//td[12]//span"
        )



        docket_sheet_urls = []
        for docket in docket_numbers:
            try:
                docket_sheet_url = results_panel.xpath(
                    ".//tr[@id = 'ctl00_ctl00_ctl00_cphMain_cphDynamicContent_cphResults_gvDocket_ctl02_ucPrintControl_printMenun1']//a"
                )[0].get("href")
            except:
                docket_sheet_url = "Docket sheet URL not found."
            finally:
                docket_sheet_urls.append(docket_sheet_url)

        summary_urls = []
        for docket in docket_numbers:
            try:
                summary_elements = results_panel.xpath(
                    ".//tr[@id = 'ctl00_ctl00_ctl00_cphMain_cphDynamicContent_cphResults_gvDocket_ctl02_ucPrintControl_printMenun2']//a"
                )
                summary_url = summary_elements[0].get("href")
            except IndexError as e:
                summary_url = "Summary URL not found"
            finally:
                summary_urls.append(summary_url)

        # check that the length of all these lists is the same, so that
        # they get zipped up properly.
        assert len(set(map(len, (
            docket_numbers, docket_sheet_urls, summary_urls,
            captions, filing_dates, case_statuses)))) == 1

        results = [
            SearchResult(
                docket_number = dn.text,
                docket_sheet_url = self.PREFIX_URL + ds,
                summary_url = self.PREFIX_URL + su,
                caption = cp.text,
                filing_date = fd.text,
                case_status = cs.text,
                otn = otn.text,
                dob = dob.text
            )
            for dn, ds, su, cp, fd, cs, otn, dob in zip(
                docket_numbers,
                docket_sheet_urls,
                summary_urls,
                captions,
                filing_dates,
                case_statuses,
                otns,
                dobs,
            )
        ]
        return results

    def search_results_from_page(self, page: str):
        """
        Given an html page's text, parse w/ lxml.html and return a list of ujs search results.


        When search results come back, there's a div w/ id 'ctl00_ctl00_ctl00_cphMain_cphDynamicContent_pnlResults'
        it has tr children for each result.
        The <td>s under this <tr> have the data on the search result.
        The first td has the a <table> inside it. That table has a <tr> and a <tbody> that just contains the image for the user to hover over.
        This same td also has div with display:none. That div has its own table nested inside.
            the first  tr/td has an <a> tag with a link to the Docket.  The second tr/td has an <a> tag with a link to the Summary.
        """
        page_tree = lxml.html.document_fromstring(page)
        results_panel = page_tree.xpath("//div[contains(@id, 'pnlResults')]")
        if len(results_panel) == 0:
            return []
        assert len(results_panel) == 1, "Did not find one and only one results panel."
        results_panel = results_panel[0]
        # Collect the columns of the table of results.
        docket_numbers = results_panel.xpath(
        ".//td[2]")
        captions = results_panel.xpath(
            ".//td[4]/span")
        filing_dates = results_panel.xpath(
            ".//td[5]"
        )
        case_statuses = results_panel.xpath(
            ".//td[7]/span")
        otns = results_panel.xpath(
            ".//td[9]/span")
        dobs = results_panel.xpath(
            ".//td[12]//span"
        )



        docket_sheet_urls = []
        for docket in docket_numbers:
            try:
                docket_sheet_url = results_panel.xpath(
                    ".//tr[@id = 'ctl00_ctl00_ctl00_cphMain_cphDynamicContent_cphResults_gvDocket_ctl02_ucPrintControl_printMenun1']//a"
                )[0].get("href")
            except:
                docket_sheet_url = "Docket sheet URL not found."
            finally:
                docket_sheet_urls.append(docket_sheet_url)

        summary_urls = []
        for docket in docket_numbers:
            try:
                summary_elements = results_panel.xpath(
                    ".//tr[@id = 'ctl00_ctl00_ctl00_cphMain_cphDynamicContent_cphResults_gvDocket_ctl02_ucPrintControl_printMenun2']//a"
                )
                summary_url = summary_elements[0].get("href")
            except IndexError as e:
                summary_url = "Summary URL not found"
            finally:
                summary_urls.append(summary_url)

        # check that the length of all these lists is the same, so that
        # they get zipped up properly.
        assert len(set(map(len, (
            docket_numbers, docket_sheet_urls, summary_urls,
            captions, filing_dates, case_statuses)))) == 1

        results = [
            SearchResult(
                docket_number = dn.text,
                docket_sheet_url = self.PREFIX_URL + ds,
                summary_url = self.PREFIX_URL + su,
                caption = cp.text,
                filing_date = fd.text,
                case_status = cs.text,
                otn = otn.text,
                dob = dob.text
            )
            for dn, ds, su, cp, fd, cs, otn, dob in zip(
                docket_numbers,
                docket_sheet_urls,
                summary_urls,
                captions,
                filing_dates,
                case_statuses,
                otns,
                dobs,
            )
        ]
        return results



    def get_select_person_search_data(self, changes):
        """
        Get a dict with the keys/values for telling the site that we would like to search for a person's 
        name.
        """
        dt = {
            '__EVENTTARGET': self.CONTROLS.SEARCH_TYPE,
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATEGENERATOR': '4AB257F3',
            '__SCROLLPOSITIONX': 0,
            '__SCROLLPOSITIONY': 0,
            self.CONTROLS.SEARCH_TYPE: 'ParticipantName',
            self.CONTROLS.COUNTY: '',
        }
        dt.update(changes)
        return dt

    def get_search_form_data(self, changes):
        dt = {
            self.CONTROLS.SEARCH_TYPE: 'ParticipantName',
            self.CONTROLS.LAST_NAME: '',
            self.CONTROLS.FIRST_NAME: '',
            self.CONTROLS.DOB: '',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsParticipantName$dpDOB$DateTextBoxMaskExtender_ClientState': '',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsParticipantName$ddlCounty':'',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsParticipantName$ddlDocketType':'',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsParticipantName$ddlCaseStatus':'',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsParticipantName$DateFiledDateRangePicker$beginDateChildControl$DateTextBox':'01/01/1950',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsParticipantName$DateFiledDateRangePicker$beginDateChildControl$DateTextBoxMaskExtender_ClientState': '',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsParticipantName$DateFiledDateRangePicker$endDateChildControl$DateTextBox':'11/21/2019',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsParticipantName$DateFiledDateRangePicker$endDateChildControl$DateTextBoxMaskExtender_ClientState':'',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$btnSearch':'Search',
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS':'',
            '__VIEWSTATEGENERATOR': '4AB257F3',
            '__SCROLLPOSITIONX': 0,
            '__SCROLLPOSITIONY': 0,
            self.CONTROLS.NONCE: '',
        }
        dt.update(changes)
        return dt

    def find_additional_page_links(self, page):
        """ Given the text of a search results page, find any links to additional results pages.

        A UJS search results page might have paginated results. Give this function the text of the first 
        page, and it will find strings identifying pages 2 through 5. 

        It will either return a list of those strings, or an empty list, if no additional pages are 
        found. 

        Another function will figure out how to use those strings in POST requests to actually 
        fetch the resources those strings point to.
        """
        # TODO There are now two functions that parse the CP search results to an lxml etree. Not DRY!
        page = lxml.html.document_fromstring(page.strip())
        pagination_span_id = "ctl00_ctl00_ctl00_cphMain_cphDynamicContent_cstPager"
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



    def get_search_pager_form_data(self, namesearch_data: dict, target: str, viewstate: str, nonce: str) -> dict:
        """
        Get the data to POST to get second, third, and so on pages of search results. 

        This takes the data posted for the original search and slightly modifies it, 
        in order to get the correct page for the same search.

        Args:
            name_search_data (dict): The dict that was POSTed to get the first search results. 
            target (str): the id of the target page to get. 
        """
        namesearch_data.pop("ctl00$ctl00$ctl00$cphMain$cphDynamicContent$btnSearch")
        namesearch_data.update({
            '__EVENTTARGET': target,
            '__VIEWSTATE': viewstate,
            '__SCROLLPOSITIONY': 490,
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsParticipantName$dpDOB$DateTextBox': '__/__/____',
            'ctl00$ctl00$ctl00$ctl07$captchaAnswer': nonce,
            'ctl00$ctl00$ctl00$ScriptManager': 'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$SearchResultsPanel|' + target,
            '__ASYNCPOST':'true',
            '': '',
        })
        return namesearch_data

    def search_results_from_updatepanel(self, text: str) -> List[dict]:
        """
        Given the text of an updatepanel response, return the cases described in that updatepanel

        The updatepanel response is a string of pipe-delimited text. The second line of that text should be 
        html describing the table of new search results. 

        This method extracts that html table, and then passes it along to a method that extracts the case information
        from that table.
        """
        patt = re.compile(".*updatePanel\|ctl00_ctl00_ctl00_cphMain_cphDynamicContent_SearchResultsPanel\|(?P<table>.*</table>).*", re.S)
        matches = patt.match(text)
        if matches is None:
            return []
        update_html = matches.group('table')
        tree = lxml.html.fromstring(update_html)
        results_table = tree.xpath("//table[@id='ctl00_ctl00_ctl00_cphMain_cphDynamicContent_cphResults_gvDocket']")
        if len(results_table) != 1:
            logger.error("update panel did not find results table.")
            return []
        results_table = results_table[0]
        return self.search_results_from_table(results_table)

    async def fetch_cases_from_additional_page(
        self, namesearch_data: dict, link: str, viewstate: str, nonce: str, 
        session, sslcontext) -> List[dict]:
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
        additional_headers = {
            'Accept': '*/*',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-MicrosoftAjax': 'Delta=true',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://ujsportal.pacourts.us',
            'Referer': 'https://ujsportal.pacourts.us/DocketSheets/MDJ.aspx',
            'Cache-Control': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36',
        }
        # yup, the site will set me change user-agent mid-session.
        # this is necessary because the ASP Update Panel feature (for updating only part of a page)
        # only works for certain user agents. 
        next_page =  await self.post(session, sslcontext, self.BASE_URL, data, additional_headers=additional_headers)
        if next_page == "":
            logging.error(f"Fetching {link} failed.")
            return []
        # parse the result pages.
        results = self.search_results_from_updatepanel(next_page)
        logger.info(f"Fetched page: {link[-12:-6]}")
        logger.info(f"  And found {len(results)} new results")
        return results



    async def search_name(self, first_name: str, last_name: str, dob: Optional[date] = None) -> dict:
        if dob:
            dob = dob.strftime(r"%m/%d/%Y")
        sslcontext = ssl.create_default_context()
        sslcontext.set_ciphers("HIGH:!DH:!aNULL")
        headers = self.__headers__
        async with aiohttp.ClientSession(headers=headers) as session:
            #request the main page
            main_page = await self.fetch(session, sslcontext, self.BASE_URL)
            assert main_page != "", "Request for landing page failed."
            logger.info("GOT main page")

            nonce = self.get_nonce(main_page)
            assert nonce is not None, "couldn't find nonce on main page."

            viewstate = self.get_viewstate(main_page)
            assert viewstate is not None, "couldn't find viewstate on main page"

            # request the name search page
            select_person_search_data = self.get_select_person_search_data({
                self.CONTROLS.NONCE: nonce,
                self.CONTROLS.VIEWSTATE: viewstate,
            })

            search_page = await self.post(session, sslcontext, self.BASE_URL,select_person_search_data)
            assert search_page != "", "Request for search page failed."

            logging.info("GOT participant search page")

            nonce = self.get_nonce(search_page)
            assert nonce is not None, "couldn't find nonce on participant search page"

            viewstate = self.get_viewstate(search_page)
            assert viewstate is not None, "couldn't find viewstate on person search page"

            # request the search results.
            search_form_data = self.get_search_form_data({
                self.CONTROLS.FIRST_NAME: first_name, 
                self.CONTROLS.LAST_NAME: last_name, 
                self.CONTROLS.DOB: dob or "",
                self.CONTROLS.NONCE: nonce,
                self.CONTROLS.VIEWSTATE: viewstate
            })
            first_search_results_page = await self.post(session, sslcontext, self.BASE_URL, data=search_form_data)
            assert first_search_results_page != "", "Request for search results failed."
            print("GOT search results back")


            nonce = self.get_nonce(first_search_results_page)
            assert nonce is not None, "couldn't find nonce on first search results page"

            viewstate = self.get_viewstate(first_search_results_page)
            assert viewstate is not None, "couldn't find viewstate on first search results page"

            results = self.search_results_from_page(first_search_results_page)

            # If there are multiple pages of search results, there will be links at the bottom
            # of the search table. 
            # If there are any such links, fetch the pages they link to.
            additional_page_links = self.find_additional_page_links(first_search_results_page)
            for link in additional_page_links:
                additional_results = await self.fetch_cases_from_additional_page(
                    namesearch_data=search_form_data.copy(), link=link, 
                    viewstate=viewstate, session=session, sslcontext=sslcontext,
                    nonce=nonce)
                results.extend(additional_results)


            logging.info(f"Found {len(results)} results")

            return results


    def parse_docket_number(self, dn: str) -> DocketNumber:
        """
        Parse the components of a MDJ Docket number.
        """
        patt = re.compile(self.DOCKET_NUMBER_REGEX, re.IGNORECASE)
        matches = patt.match(dn)
        if not matches:
            raise ValueError(f"{dn} was not a correctly formatted docket number.")
        return DocketNumber(
            court = matches.group('court'),
            county = matches.group('county'),
            office = matches.group('office'),
            dkt_type = matches.group('dkt_type'),
            sequence = matches.group('sequence'),
            year = matches.group('year'),
            )

    def lookup_county(self, county_code, office_code):
        """ Maps county numbers from a docket number (41, 20, etc.) to county
        names.


        The MDJ Docket search requires a user to select the name of the county
        to search. We can get the name of the county from a Docket Number, but it
        is not straightforward.

        MDJ Docket numbers start with "MDJ-012345". The five digits are a
        county code and an office code. Some counties share the same code, so the
        name of a county depends on all five of these digits.

        This method uses a reference table to match the county and office codes
        to the correct county's name.

        Args:
            county_code (str): Two-digit code that (usually) identifies a county.
            office_code (str): Three more digits that are sometimes necessary to
            identify a county, when two counties share the same county code.

        Returns:
            The name of a county, or None, if no match was found. Raise an
            AssertionError if multiple matches were found, because then something
            is wrong with the reference table.

        """
        full_five_digits = "{}{}".format(county_code, office_code)

        lookup_table_path = os.path.join(os.path.split(ujs_search.__file__)[0], "reference/county_lookup.csv")

        with open(lookup_table_path, "r") as f:
            reader = csv.DictReader(f)
            matches = []
            for row in reader:
                if re.match(row["regex"], full_five_digits):
                    matches.append(row["County"])
        assert len(matches) <= 1, "Error: Found multiple matches for {}".format(
            full_five_digits)
        if len(matches) == 0:
            return None
        return matches[0]

    def get_select_county_data(self, county, nonce, viewstate):
        return {
            "__EVENTTARGET": "ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$ddlCounty",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": "4AB257F3",
            "__SCROLLPOSITIONX": "0",
            "__SCROLLPOSITIONY": "0",
            "ctl00$ctl00$ctl00$cphMain$cphDynamicContent$ddlSearchType": "DocketNumber",
            "ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$ddlCounty": county,
            "ctl00$ctl00$ctl00$ctl07$captchaAnswer": nonce,
        }

    def combine_office_code(self, county, office):
        """
        Combine county and office codes into one for or five digit code for POSTing.

        MDJ docket numbers include a five-digit code that's the concatenation of the county and office codes
        for a case. But for whatever reason, the POST requires that if the county code starts w/ a 0, the
        leading 0 gets cut. 

        For ex., Alleheny is 05, so while a docket might have the number MD-05101-CR-1234567-2020, the 
        POST requires the 05101 to be shortened to 5101.
        """
        return f"{county.lstrip('0')}{office}"

    def get_select_office_data(self, base, county, office, nonce, viewstate):

        office_code = self.combine_office_code(county, office)
       
        base.update({
            "__VIEWSTATE": viewstate,
            "__EVENTTARGET": "ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$ddlCourtOffice",
            "ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$ddlCourtOffice": office_code,
            "ctl00$ctl00$ctl00$ctl07$captchaAnswer": nonce,
        })
        return base


    def get_docket_search_data(self, base, dn, nonce, viewstate):
        base.update({
            "__EVENTTARGET":"",
            "__VIEWSTATE": viewstate,
            "ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$ddlDocketType": dn.dkt_type,
            "ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$txtSequenceNumber": dn.sequence,
            "ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$txtYear": dn.year,
            "ctl00$ctl00$ctl00$cphMain$cphDynamicContent$btnSearch": "Search",
            "ctl00$ctl00$ctl00$ctl07$captchaAnswer": nonce,
        })
        return base

    async def search_docket_number(self, docket_number: str) -> dict:
        docket_number = docket_number.upper()
        dn = self.parse_docket_number(docket_number)
        county_name = self.lookup_county(dn.county, dn.office)
        sslcontext = ssl.create_default_context()
        sslcontext.set_ciphers("HIGH:!DH:!aNULL")
        async with aiohttp.ClientSession(headers=self.__headers__) as session:

            # parse the components of the docket number.

            # get the main page
            main_page = await self.fetch(session, sslcontext, self.BASE_URL)
            if main_page == "": return [{"errors": "Failed to get main page"}]

            # select the county
            viewstate = self.get_viewstate(main_page)
            nonce = self.get_nonce(main_page)
            county_select_data = self.get_select_county_data(county = county_name, nonce = nonce, viewstate = viewstate)
            county_select_page = await self.post(
                session, sslcontext, self.BASE_URL, data = county_select_data)
            if county_select_page == "": return [{"errors": "Failed to select county"}]

            # select the court office
            viewstate = self.get_viewstate(county_select_page)
            nonce = self.get_nonce(county_select_page)
            office_select_data = self.get_select_office_data(
                base = county_select_data, office = dn.office, county=dn.county, nonce=nonce, viewstate=viewstate)           
            office_select_page = await self.post(
                session, sslcontext, self.BASE_URL, data=office_select_data)
            if office_select_page == "": return [{"errors": "Failed to select office"}]

            # POST the search
            viewstate = self.get_viewstate(office_select_page)
            nonce = self.get_nonce(office_select_page)
            docket_search_data = self.get_docket_search_data(
                office_select_data, dn, nonce=nonce, viewstate=viewstate)
            docket_search_page = await self.post(
                session, sslcontext, self.BASE_URL, data=docket_search_data)
            if docket_search_page == "": return [{"errors": "Failed to get search results page"}]

            # parse the results.
            results = self.search_results_from_page(docket_search_page)
            return results