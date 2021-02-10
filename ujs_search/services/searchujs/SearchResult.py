from dataclasses import dataclass


@dataclass
class SearchResult:
    """
    A single row of a resulting case found by searching the UJS portal.
    """

    docket_number: str
    court: str
    docket_sheet_url: str
    summary_url: str
    caption: str
    filing_date: str
    case_status: str
    caption: str
    otn: str
    dob: str
    participants: str