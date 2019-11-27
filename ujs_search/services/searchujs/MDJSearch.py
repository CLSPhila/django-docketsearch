from .UJSSearch import UJSSearch
from .SearchResult import SearchResult
from lxml import etree
import lxml.html
import re
import time
import logging
from typing import List, Optional
from datetime import date
logger = logging.getLogger(__name__)






class MDJSearch(UJSSearch):
    BASE_URL = "https://ujsportal.pacourts.us/DocketSheets/MDJ.aspx"

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


    def search_results_from_page(self, page):
        """
        Given a parsed html page, (parsed w/ lxml.html), return a list of ujs search results.
        When search results come back, there's a div w/ id 'ctl00_ctl00_ctl00_cphMain_cphDynamicContent_pnlResults'
        it has tr children for each result.
        The <td>s under this <tr> have the data on the search result.
        The first td has the a <table> inside it. That table has a <tr> and a <tbody> that just contains the image for the user to hover over.
        This same td also has div with display:none. That div has its own table nested inside.
            the first  tr/td has an <a> tag with a link to the Docket.  The second tr/td has an <a> tag with a link to the Summary.
        """
        results_panel = page.xpath("//div[@id='ctl00_ctl00_ctl00_cphMain_cphDynamicContent_pnlResults']")
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

        parsed_page = lxml.html.document_fromstring(search_results_page.text)
        results = self.search_results_from_page(parsed_page)

        logging.info(f"Found {len(results)} results")

        return results


    def search_docket_number(self, docket_number: str) -> dict:
        raise NotImplementedError