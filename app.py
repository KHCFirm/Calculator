import datetime as dt
import json
from functools import lru_cache

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
def get_us_holidays_for_year(year: int) -> set:
    """
    Return a set of US federal holidays (observed dates) for a given year.
    """
    holidays = []

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


def calculate_business_dates(start_date: dt.date, business_days: int) -> list[dt.date]:
    """
    Return a list of business dates, counting start_date as Day 1
    if it is a business day. List length == business_days when successful.
    """
    dates: list[dt.date] = []
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


st.set_page_config(page_title="30 Business Day Calculator", layout="centered")

# Make the app look like a small floating widget and force white card even in dark mode
st.markdown(
    """
    <style>
    .stApp {
        background-color: #111827;
    }
    .main .block-container {
        max-width: 380px;
        padding: 1.5rem 1.25rem;
        position: fixed;
        top: 1rem;
        right: 1rem;
        background: #ffffff !important;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.16);
        border-radius: 12px;
        color: #111827 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("30 Business Day Calculator")

st.write(
    "Enter a start date in **MM/DD/YYYY** format. The app will calculate "
    "the date that is **30 business days** away, counting the start date "
    "as **Day 1**, and skipping weekends and U.S. federal holidays."
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

final_date = None
error_msg = None

if start_date_str.strip():
    try:
        # Parse MM/DD/YYYY
        month, day, year = start_date_str.strip().split("/")
        start_date = dt.date(int(year), int(month), int(day))

        business_dates = calculate_business_dates(start_date, business_days_to_add)

        if len(business_dates) < business_days_to_add:
            error_msg = "Could not compute the full range of business days."
        else:
            final_date = business_dates[-1]
    except ValueError:
        error_msg = "Please enter a valid date in MM/DD/YYYY format."

# Show result or error
if error_msg:
    st.error(error_msg)
elif final_date:
    formatted_final = final_date.strftime("%m/%d/%Y")

    st.subheader("Result")

    # Render result + copy button with JS in a small iframe component
    components.html(
        f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-top: 0.25rem;">
            <span id="result-date"
                  style="font-size: 32px; font-weight: 700; letter-spacing: 0.5px; color: #111827;">
                {formatted_final}
            </span>
            <button id="copy-date-btn"
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
        height=80,
        scrolling=False,
    )
