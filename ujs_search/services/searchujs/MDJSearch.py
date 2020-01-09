from .UJSSearch import UJSSearch
from .SearchResult import SearchResult
from lxml import etree
import lxml.html
import re
import ssl
import aiohttp
import time
import logging
from typing import List, Optional
from collections import namedtuple
from datetime import date
import csv


logger = logging.getLogger(__name__)
DocketNumber = namedtuple('DocketNumber', 'court county office dkt_type sequence year')



class MDJSearch(UJSSearch):
    BASE_URL = "https://ujsportal.pacourts.us/DocketSheets/MDJ.aspx"
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
        page = lxml.html.document_fromstring(page)
        results_panel = page.xpath("//div[contains(@id, 'pnlResults')]")
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
                summary_url = results_panel.xpath(
                    ".//tr[@id = 'ctl00_ctl00_ctl00_cphMain_cphDynamicContent_cphResults_gvDocket_ctl02_ucPrintControl_printMenun2']//a"
                )[0].get("href")
            except NoSuchElementException:
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
                docket_sheet_url = ds,
                summary_url = su,
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



    def search_name(self, first_name: str, last_name: str, dob: Optional[date] = None) -> dict:
        if dob:
            dob = dob.strftime(r"%m/%d/%Y")
        #request the main page
        main_page = self.sess.get(self.BASE_URL)
        assert main_page.status_code == 200, "Request for landing page failed."
        logger.info("GOT main page")
        time.sleep(1)

        nonce = self.get_nonce(main_page)
        assert nonce is not None, "couldn't find nonce on main page."

        viewstate = self.get_viewstate(main_page)
        assert viewstate is not None, "couldn't find viewstate on main page"

        # request the name search page
        select_person_search_data = self.get_select_person_search_data({
            self.CONTROLS.NONCE: nonce,
            self.CONTROLS.VIEWSTATE: viewstate,
        })

        search_page = self.sess.post(self.BASE_URL, data=select_person_search_data)
        assert search_page.status_code == 200, "Request for search page failed."

        logging.info("GOT participant search page")
        #with open("participantSearch.html", "wb") as f:
        #    f.write(search_page.content)
        time.sleep(1)

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
        search_results_page = self.sess.post(self.BASE_URL, data=search_form_data)
        assert search_results_page.status_code == 200, "Request for search results failed."
        print("GOT search results back")

        #with open("participantSearchResults.html", "wb") as f:
        #    f.write(search_results_page.content)

        results = self.search_results_from_page(search_results_page.text)

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
        with open("reference/county_lookup.csv", "r") as f:
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
            with open("../out3.html","w") as f: f.write(docket_search_page)

            # parse the results.
            results = self.search_results_from_page(docket_search_page)
            return results