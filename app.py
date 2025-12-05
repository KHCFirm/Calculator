import datetime as dt
import json
from functools import lru_cache
from typing import List, Set

import streamlit as st
import streamlit.components.v1 as components


# --------------------- Holiday helpers ---------------------


def nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> dt.date:
    """
    Return the date of the n-th given weekday in a month.
    month: 1-12, weekday: 0=Monday..6=Sunday, n>=1
    weekday uses Python convention: Monday=0..Sunday=6.
    """
    date = dt.date(year, month, 1)
    while date.weekday() != weekday:
        date += dt.timedelta(days=1)
    date += dt.timedelta(weeks=n - 1)
    return date


def last_weekday_of_month(year: int, month: int, weekday: int) -> dt.date:
    """
    Return the date of the last given weekday in a month.
    month: 1-12, weekday: 0=Monday..6=Sunday
    """
    if month == 12:
        next_month = dt.date(year + 1, 1, 1)
    else:
        next_month = dt.date(year, month + 1, 1)
    date = next_month - dt.timedelta(days=1)
    while date.weekday() != weekday:
        date -= dt.timedelta(days=1)
    return date


def observed_date(date: dt.date) -> dt.date:
    """
    If holiday falls on Saturday -> observed Friday.
    If holiday falls on Sunday -> observed Monday.
    Otherwise, observe on the same day.
    """
    if date.weekday() == 5:  # Saturday
        return date - dt.timedelta(days=1)
    if date.weekday() == 6:  # Sunday
        return date + dt.timedelta(days=1)
    return date


@lru_cache(maxsize=None)
def get_us_holidays_for_year(year: int) -> Set[dt.date]:
    """
    Return a set of US federal holidays (observed dates) for a given year.
    """
    holidays: List[dt.date] = []

    # 1. New Year's Day (Jan 1)
    new_year = dt.date(year, 1, 1)
    holidays.append(observed_date(new_year))

    # 2. MLK Day (3rd Monday in January)
    holidays.append(nth_weekday_of_month(year, 1, weekday=0, n=3))  # Monday

    # 3. Presidents Day (3rd Monday in February)
    holidays.append(nth_weekday_of_month(year, 2, weekday=0, n=3))

    # 4. Memorial Day (last Monday in May)
    holidays.append(last_weekday_of_month(year, 5, weekday=0))

    # 5. Juneteenth (June 19, observed)
    juneteenth = dt.date(year, 6, 19)
    holidays.append(observed_date(juneteenth))

    # 6. Independence Day (July 4, observed)
    independence = dt.date(year, 7, 4)
    holidays.append(observed_date(independence))

    # 7. Labor Day (1st Monday in September)
    holidays.append(nth_weekday_of_month(year, 9, weekday=0, n=1))

    # 8. Columbus Day / Indigenous Peoples' Day (2nd Monday in October)
    holidays.append(nth_weekday_of_month(year, 10, weekday=0, n=2))

    # 9. Veterans Day (Nov 11, observed)
    veterans = dt.date(year, 11, 11)
    holidays.append(observed_date(veterans))

    # 10. Thanksgiving Day (4th Thursday in November)
    holidays.append(nth_weekday_of_month(year, 11, weekday=3, n=4))  # Thursday

    # 11. Christmas Day (Dec 25, observed)
    christmas = dt.date(year, 12, 25)
    holidays.append(observed_date(christmas))

    return set(holidays)


def is_federal_holiday(date: dt.date) -> bool:
    return date in get_us_holidays_for_year(date.year)


def is_weekend(date: dt.date) -> bool:
    # Monday=0 .. Sunday=6
    return date.weekday() >= 5


def is_business_day(date: dt.date) -> bool:
    return not is_weekend(date) and not is_federal_holiday(date)


def calculate_business_dates(start_date: dt.date, business_days: int) -> List[dt.date]:
    """
    Return a list of business dates, counting start_date as Day 1
    if it is a business day. List length == business_days when successful.
    """
    dates: List[dt.date] = []
    current = start_date
    count = 0

    while count < business_days:
        if is_business_day(current):
            dates.append(current)
            count += 1
            if count == business_days:
                break
        current += dt.timedelta(days=1)

    return dates


# --------------------- Streamlit UI ---------------------


st.set_page_config(
    page_title="30 Business Day Calculator",
    page_icon="📅",
    layout="centered",
)

# Global styling for card + theme-aware colors, and remove the top white "bubble"
st.markdown(
    """
    <style>
    /* Remove Streamlit default header/decor bubble */
    header {visibility: hidden;}
    section[data-testid="stDecoration"] {display: none;}
    [data-testid="stHeader"] {height: 0px !important;}
    .stApp {padding-top: 0 !important;}

    :root {
        --card-radius: 16px;
        --card-padding-y: 1.6rem;
        --card-padding-x: 1.6rem;
    }

    .main .block-container {
        max-width: 420px;
        padding-top: 2.5rem !important;
        padding-bottom: 3rem;
    }

    /* Light mode */
    @media (prefers-color-scheme: light) {
        .stApp {
            background: #f3f4f6;
        }
        .app-card {
            background: #ffffff;
            color: #0f172a;
            border: 1px solid rgba(148, 163, 184, 0.35);
            box-shadow: 0 18px 35px rgba(15, 23, 42, 0.10);
        }
        .app-subtitle {
            color: #475569;
        }
    }

    /* Dark mode */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background: radial-gradient(circle at top, #0f172a 0%, #020617 70%);
        }
        .app-card {
            background: #020617;
            color: #e5e7eb;
            border: 1px solid rgba(148, 163, 184, 0.4);
            box-shadow: 0 18px 40px rgba(0, 0, 0, 0.75);
        }
        .app-subtitle {
            color: #94a3b8;
        }
    }

    .app-card {
        border-radius: var(--card-radius);
        padding: var(--card-padding-y) var(--card-padding-x) 2rem var(--card-padding-x);
    }

    .app-header-icon {
        font-size: 32px;
        margin-bottom: 0.4rem;
    }

    .app-title {
        font-size: 1.6rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }

    .app-subtitle {
        font-size: 0.92rem;
        margin-top: 0rem;
        margin-bottom: 1.2rem;
        line-height: 1.4rem;
    }

    .stTextInput label {
        font-weight: 600;
        margin-bottom: 0.2rem;
        font-size: 0.9rem;
    }

    .stTextInput > div > div > input {
        border-radius: 8px;
        padding: 0.45rem 0.8rem;
        border: 1px solid rgba(148, 163, 184, 0.45);
        font-size: 0.92rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----- Card wrapper open -----
st.markdown('<div class="app-card">', unsafe_allow_html=True)

# Icon (no bubble) + title/subtitle
st.markdown('<div class="app-header-icon">📅</div>', unsafe_allow_html=True)
st.markdown('<div class="app-title">30 Business Day Calculator</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">'
    "Enter a start date in <strong>MM/DD/YYYY</strong> format. "
    "The start date counts as <strong>Day 1</strong>. "
    "Weekends and U.S. federal holidays are skipped."
    "</div>",
    unsafe_allow_html=True,
)

business_days_to_add = 30
today = dt.date.today()
default_str = today.strftime("%m/%d/%Y")

# Text input so Enter triggers a rerun naturally
start_date_str = st.text_input(
    "Start date (MM/DD/YYYY)",
    value=default_str,
    help="Example: 03/15/2025",
)

final_date: dt.date | None = None
error_msg: str | None = None

if start_date_str.strip():
    try:
        # Parse MM/DD/YYYY
        month_str, day_str, year_str = start_date_str.strip().split("/")
        start_date = dt.date(int(year_str), int(month_str), int(day_str))

        business_dates = calculate_business_dates(start_date, business_days_to_add)

        if len(business_dates) < business_days_to_add:
            error_msg = "Could not compute the full range of business days."
        else:
            final_date = business_dates[-1]
    except ValueError:
        error_msg = "Please enter a valid date in MM/DD/YYYY format (e.g., 03/15/2025)."

# Show result or error
if error_msg:
    st.error(error_msg)
elif final_date:
    formatted_final = final_date.strftime("%m/%d/%Y")

    st.subheader("Result")

    # Theme-aware result styling with copy button
    components.html(
        f"""
        <style>
        /* Default (light) */
        .result-date {{
            color: #000000;
        }}
        .copy-btn {{
            color: #000000;
        }}

        /* Dark mode */
        @media (prefers-color-scheme: dark) {{
            .result-date {{
                color: #ffffff !important;
            }}
            .copy-btn {{
                color: #ffffff !important;
            }}
        }}
        </style>

        <div style="display: flex; align-items: center; gap: 10px; margin-top: 0.25rem;">
            <span class="result-date"
                  style="font-size: 32px; font-weight: 700; letter-spacing: 0.5px;">
                {formatted_final}
            </span>
            <button id="copy-date-btn"
                    class="copy-btn"
                    style="border: none; background: transparent; cursor: pointer; font-size: 20px;"
                    aria-label="Copy result date">
                📋
            </button>
        </div>

        <script>
        (function() {{
          const btn = document.getElementById('copy-date-btn');
          if (!btn) return;
          btn.addEventListener('click', async () => {{
            try {{
              await navigator.clipboard.writeText({json.dumps(formatted_final)});
              btn.textContent = '✅';
              setTimeout(() => btn.textContent = '📋', 1200);
            }} catch (err) {{
              console.error('Copy failed', err);
            }}
          }});
        }})();
        </script>
        """,
        height=90,
        scrolling=False,
    )

# ----- Card wrapper close -----
st.markdown("</div>", unsafe_allow_html=True)
