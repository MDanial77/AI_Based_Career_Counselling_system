import os
import json
from datetime import datetime, timedelta, timezone
from statistics import median
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


# ==========================================================
# CONFIGURATION
# ==========================================================

ADZUNA_COUNTRY = os.getenv(
    "ADZUNA_COUNTRY",
    "gb"
).strip().lower()

REQUEST_TIMEOUT = 8
RESULTS_PER_PAGE = 20
MAX_DISPLAY_JOBS = 5
RECENT_DAYS = 60

# Only use plausible annual GB salary figures in salary statistics.
# This prevents hourly/daily values such as £25 from distorting
# annual salary insights.
MIN_ANNUAL_SALARY = 10000
MAX_ANNUAL_SALARY = 500000


# ==========================================================
# CAREER SEARCH RULES
# ==========================================================

CAREER_SEARCH_RULES = {

    "dentist": {
        "query": "dentist",
        "include": [
            "dentist",
            "dental officer",
            "dental surgeon"
        ],
        "exclude": [
            "nurse",
            "trainee",
            "receptionist",
            "assistant"
        ]
    },

    "doctor": {
        "query": "doctor",
        "include": [
            "doctor",
            "physician",
            "medical officer"
        ],
        "exclude": [
            "account manager",
            "sales",
            "recruitment"
        ]
    },

    "pharmacist": {
        "query": "pharmacist",
        "include": [
            "pharmacist"
        ],
        "exclude": [
            "dispenser",
            "assistant",
            "technician"
        ]
    },

    "software engineer": {
        "query": "software engineer",
        "include": [
            "software engineer",
            "software developer"
        ],
        "exclude": []
    },

    "ai engineer": {
        "query": "machine learning engineer",
        "include": [
            "machine learning engineer",
            "ai engineer",
            "artificial intelligence engineer"
        ],
        "exclude": []
    },

    "data scientist": {
        "query": "data scientist",
        "include": [
            "data scientist"
        ],
        "exclude": []
    },

    "web developer": {
        "query": "web developer",
        "include": [
            "web developer",
            "frontend developer",
            "front end developer",
            "backend developer",
            "back end developer",
            "full stack developer"
        ],
        "exclude": []
    },

    "cyber security analyst": {
        "query": "cyber security analyst",
        "include": [
            "cyber security",
            "cybersecurity",
            "security analyst"
        ],
        "exclude": []
    },

    "graphic designer": {
        "query": "graphic designer",
        "include": [
            "graphic designer",
            "visual designer"
        ],
        "exclude": []
    },

    "animator": {
        "query": "animator",
        "include": [
            "animator",
            "animation artist",
            "3d animator",
            "2d animator"
        ],
        "exclude": []
    },

    "accountant": {
        "query": "accountant",
        "include": [
            "accountant"
        ],
        "exclude": []
    },

    "bank manager": {
        "query": "bank manager",
        "include": [
            "bank manager",
            "banking manager",
            "bank branch manager"
        ],
        "exclude": []
    },

    "marketing manager": {
        "query": "marketing manager",
        "include": [
            "marketing manager"
        ],
        "exclude": []
    },

    "civil engineer": {
        "query": "civil engineer",
        "include": [
            "civil engineer"
        ],
        "exclude": []
    },

    "mechanical engineer": {
        "query": "mechanical engineer",
        "include": [
            "mechanical engineer"
        ],
        "exclude": []
    },

    "electrical engineer": {
        "query": "electrical engineer",
        "include": [
            "electrical engineer"
        ],
        "exclude": []
    },

    "teacher": {
        "query": "teacher",
        "include": [
            "teacher"
        ],
        "exclude": [
            "teaching assistant"
        ]
    },

    "lecturer": {
        "query": "lecturer",
        "include": [
            "lecturer"
        ],
        "exclude": []
    },

    "lawyer": {
        "query": "lawyer",
        "include": [
            "lawyer",
            "solicitor",
            "legal counsel"
        ],
        "exclude": [
            "legal assistant",
            "legal secretary"
        ]
    },

    # CSS Officer is Pakistan-specific, while the current
    # live source is configured for the GB market.
    "css officer": {
        "enabled": False,
        "message": (
            "Live GB job-market data is not directly applicable "
            "to the CSS Officer career."
        )
    }
}


# ==========================================================
# EMPTY / ERROR RESPONSE
# ==========================================================

def _empty_market_result(
    message,
    career_name=""
):

    return {
        "available": False,

        "career": career_name,

        "country": ADZUNA_COUNTRY.upper(),

        "total_jobs": 0,

        "relevant_jobs_found": 0,

        "market_activity": "Unavailable",

        "salary_insights": {
            "available": False,
            "currency": "GBP",
            "sample_size": 0,
            "minimum": None,
            "maximum": None,
            "average": None,
            "median": None,
            "reliability": "No Salary Data"
        },

        "jobs": [],

        "message": message
    }


# ==========================================================
# DATE PARSER
# ==========================================================

def _parse_created_date(
    created_text
):

    if not created_text:
        return None

    try:

        return datetime.fromisoformat(
            created_text.replace(
                "Z",
                "+00:00"
            )
        )

    except (ValueError, TypeError):
        return None


# ==========================================================
# SAFE NUMBER CONVERSION
# ==========================================================

def _to_float(
    value
):

    try:

        if value is None:
            return None

        return float(value)

    except (ValueError, TypeError):
        return None


# ==========================================================
# LIVE SALARY ANALYSIS
# ==========================================================

def _calculate_salary_insights(jobs):

    minimum_salaries = []
    maximum_salaries = []
    midpoint_salaries = []


    for job in jobs:

        salary_min = _to_float(
            job.get("salary_min")
        )

        salary_max = _to_float(
            job.get("salary_max")
        )


        # --------------------------------------------------
        # KEEP ONLY PLAUSIBLE ANNUAL SALARY VALUES
        # --------------------------------------------------

        if (
            salary_min is not None
            and not (
                MIN_ANNUAL_SALARY
                <= salary_min
                <= MAX_ANNUAL_SALARY
            )
        ):
            salary_min = None


        if (
            salary_max is not None
            and not (
                MIN_ANNUAL_SALARY
                <= salary_max
                <= MAX_ANNUAL_SALARY
            )
        ):
            salary_max = None


        if salary_min is not None:
            minimum_salaries.append(
                salary_min
            )


        if salary_max is not None:
            maximum_salaries.append(
                salary_max
            )


        if (
            salary_min is not None
            and salary_max is not None
        ):

            midpoint_salaries.append(
                (
                    salary_min
                    + salary_max
                )
                / 2
            )


        elif salary_min is not None:

            midpoint_salaries.append(
                salary_min
            )


        elif salary_max is not None:

            midpoint_salaries.append(
                salary_max
            )


    if not midpoint_salaries:

        return {
            "available": False,
            "currency": "GBP",
            "sample_size": 0,
            "minimum": None,
            "maximum": None,
            "average": None,
            "median": None,
            "reliability": "No Salary Data"
        }


    minimum_salary = (

        min(minimum_salaries)

        if minimum_salaries

        else min(midpoint_salaries)
    )


    maximum_salary = (

        max(maximum_salaries)

        if maximum_salaries

        else max(midpoint_salaries)
    )


    average_salary = (
        sum(midpoint_salaries)
        / len(midpoint_salaries)
    )

    median_salary = median(
        midpoint_salaries
    )


    sample_size = len(
        midpoint_salaries
    )


    if sample_size >= 10:
        reliability = "Good Sample"

    elif sample_size >= 5:
        reliability = "Moderate Sample"

    elif sample_size >= 2:
        reliability = "Small Sample"

    else:
        reliability = "Single Listing"


    return {
        "available": True,
        "currency": "GBP",

        "sample_size": sample_size,

        "minimum": round(
            minimum_salary,
            2
        ),

        "maximum": round(
            maximum_salary,
            2
        ),

        "average": round(
            average_salary,
            2
        ),

        "median": round(
            median_salary,
            2
        ),

        "reliability": reliability
    }
def _detect_seniority(title):

    title_lower = str(
        title or ""
    ).lower()


    entry_keywords = [
        "junior",
        "graduate",
        "trainee",
        "entry level",
        "entry-level",
        "apprentice"
    ]


    senior_keywords = [
        "senior",
        "lead",
        "principal",
        "staff",
        "director",
        "manager",
        "head of",
        "chief"
    ]


    if any(
        keyword in title_lower
        for keyword in entry_keywords
    ):
        return "Entry / Junior"


    if any(
        keyword in title_lower
        for keyword in senior_keywords
    ):
        return "Senior / Management"


    return "General"

# ==========================================================
# MAIN JOB-MARKET FUNCTION
# ==========================================================

def get_job_market_data(
    career_name
):

    career_name = str(
        career_name or ""
    ).strip()


    # ------------------------------------------------------
    # VALIDATE CAREER NAME
    # ------------------------------------------------------

    if not career_name:

        return _empty_market_result(
            "Career name was not provided."
        )


    # ------------------------------------------------------
    # READ API CREDENTIALS
    # ------------------------------------------------------

    app_id = os.getenv(
        "ADZUNA_APP_ID"
    )

    app_key = os.getenv(
        "ADZUNA_APP_KEY"
    )


    if not app_id or not app_key:

        return _empty_market_result(
            "Live job market data is not configured.",
            career_name
        )


    # ------------------------------------------------------
    # CAREER SEARCH CONFIGURATION
    # ------------------------------------------------------

    career_key = career_name.lower()


    search_rule = CAREER_SEARCH_RULES.get(
        career_key,
        {
            "enabled": True,
            "query": career_name,
            "include": [
                career_key
            ],
            "exclude": []
        }
    )


    # ------------------------------------------------------
    # CAREER NOT SUPPORTED BY CURRENT MARKET SOURCE
    # ------------------------------------------------------

    if search_rule.get(
        "enabled"
    ) is False:

        return _empty_market_result(

            search_rule.get(
                "message",
                (
                    "Live market data is not "
                    "available for this career."
                )
            ),

            career_name
        )


    query = search_rule.get(
        "query",
        career_name
    )


    include_keywords = [

        str(keyword)
        .strip()
        .lower()

        for keyword
        in search_rule.get(
            "include",
            []
        )

        if str(keyword).strip()
    ]


    exclude_keywords = [

        str(keyword)
        .strip()
        .lower()

        for keyword
        in search_rule.get(
            "exclude",
            []
        )

        if str(keyword).strip()
    ]


    # ------------------------------------------------------
    # API URL
    # ------------------------------------------------------

    url = (
        "https://api.adzuna.com/"
        "v1/api/jobs/"
        f"{ADZUNA_COUNTRY}/search/1"
    )


    # ------------------------------------------------------
    # API PARAMETERS
    # ------------------------------------------------------

    params = {

        "app_id": app_id,

        "app_key": app_key,

        "results_per_page":
            RESULTS_PER_PAGE,

        "what": query,

        "content-type":
            "application/json"
    }


    try:

        # ==================================================
        # API REQUEST
        # ==================================================

        request_url = (
            f"{url}?{urlencode(params)}"
        )
        request = Request(
            request_url,
            headers={"Accept": "application/json"}
        )

        with urlopen(
            request,
            timeout=REQUEST_TIMEOUT
        ) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )


        # --------------------------------------------------
        # VALIDATE RESPONSE
        # --------------------------------------------------

        if not isinstance(
            data,
            dict
        ):

            return _empty_market_result(
                (
                    "Unexpected data received "
                    "from the job-market service."
                ),
                career_name
            )


        api_results = data.get(
            "results",
            []
        )


        if not isinstance(
            api_results,
            list
        ):

            api_results = []


        # ==================================================
        # RECENCY FILTER
        # ==================================================

        cutoff_date = (
            datetime.now(
                timezone.utc
            )
            - timedelta(
                days=RECENT_DAYS
            )
        )


        all_relevant_jobs = []


        # ==================================================
        # PROCESS API JOBS
        # ==================================================

        for job in api_results:


            if not isinstance(
                job,
                dict
            ):

                continue


            title = str(
                job.get(
                    "title"
                )
                or ""
            ).strip()


            if not title:
                continue


            title_lower = (
                title.lower()
            )


            # ----------------------------------------------
            # CAREER TITLE MUST MATCH
            # ----------------------------------------------

            include_match = (

                not include_keywords

                or any(

                    keyword
                    in title_lower

                    for keyword
                    in include_keywords
                )
            )


            if not include_match:
                continue


            # ----------------------------------------------
            # REMOVE IRRELEVANT TITLES
            # ----------------------------------------------

            exclude_match = any(

                keyword
                in title_lower

                for keyword
                in exclude_keywords
            )


            if exclude_match:
                continue


            # ----------------------------------------------
            # REMOVE OLD JOBS
            # ----------------------------------------------

            created_text = job.get(
                "created"
            )


            created_date = (
                _parse_created_date(
                    created_text
                )
            )


            if (
                created_date is not None
                and created_date
                < cutoff_date
            ):

                continue


            # ----------------------------------------------
            # COMPANY
            # ----------------------------------------------

            company_data = (

                job.get("company")

                if isinstance(
                    job.get(
                        "company"
                    ),
                    dict
                )

                else {}
            )


            # ----------------------------------------------
            # LOCATION
            # ----------------------------------------------

            location_data = (

                job.get("location")

                if isinstance(
                    job.get(
                        "location"
                    ),
                    dict
                )

                else {}
            )


            # ----------------------------------------------
            # SAVE RELEVANT JOB
            # ----------------------------------------------

            all_relevant_jobs.append({

                "title": title,
                "seniority": _detect_seniority(title),

                "company":
                    company_data.get(
                        "display_name",
                        "Company not specified"
                    ),

                "location":
                    location_data.get(
                        "display_name",
                        "Location not specified"
                    ),

                "salary_min":
                    _to_float(
                        job.get(
                            "salary_min"
                        )
                    ),

                "salary_max":
                    _to_float(
                        job.get(
                            "salary_max"
                        )
                    ),

                "created":
                    created_text,

                "url":
                    job.get(
                        "redirect_url"
                    )
            })


        # ==================================================
        # NUMBER OF RELEVANT RECENT JOBS
        # ==================================================

        relevant_jobs_found = len(
            all_relevant_jobs
        )


        # ==================================================
        # MARKET ACTIVITY
        # ==================================================

        if relevant_jobs_found >= 10:

            market_activity = (
                "Strong"
            )


        elif relevant_jobs_found >= 5:

            market_activity = (
                "Moderate"
            )


        elif relevant_jobs_found >= 1:

            market_activity = (
                "Limited"
            )


        else:

            market_activity = (
                "No Recent Matches"
            )


        seniority_priority = {
            "Entry / Junior": 0,
            "General": 1,
            "Senior / Management": 2
        }


        all_relevant_jobs.sort(
            key=lambda job: seniority_priority.get(
                job.get(
                    "seniority",
                    "General"
                ),
                1
            )
        )


        # ==================================================
        # ONLY DISPLAY TOP 5 JOBS
        # ==================================================

        display_jobs = (
            all_relevant_jobs[
                :MAX_DISPLAY_JOBS
            ]
        )


        # ==================================================
        # LIVE SALARY INSIGHTS
        # ==================================================

        salary_insights = (
            _calculate_salary_insights(
                all_relevant_jobs
            )
        )


        # ==================================================
        # RETURN LIVE MARKET DATA
        # ==================================================

        return {

            "available": True,

            "career":
                career_name,

            "country":
                ADZUNA_COUNTRY.upper(),

            "query":
                query,

            # Broad API search count
            "total_jobs":
                int(
                    data.get(
                        "count",
                        0
                    )
                    or 0
                ),

            # Relevant jobs found in the
            # fetched recent sample
            "relevant_jobs_found":
                relevant_jobs_found,

            "market_activity":
                market_activity,

            "salary_insights":
                salary_insights,

            "searched_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "jobs":
                display_jobs,

            "message": (
                "Current job-market data "
                "retrieved successfully."
            )
        }


    # ======================================================
    # ERROR HANDLING
    # ======================================================

    except TimeoutError:

        return _empty_market_result(
            (
                "The job-market service took "
                "too long to respond."
            ),
            career_name
        )


    except HTTPError:

        return _empty_market_result(
            (
                "The job-market service "
                "returned an HTTP error."
            ),
            career_name
        )


    except URLError:

        return _empty_market_result(
            (
                "Unable to connect to the "
                "live job-market service."
            ),
            career_name
        )


    except ValueError:

        return _empty_market_result(
            (
                "Invalid response received "
                "from the job-market service."
            ),
            career_name
        )