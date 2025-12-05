import datetime as dt
import json
from functools import lru_cache
from string import Template

import streamlit as st


# --------------------- Holiday helpers ---------------------

def nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> dt.date:
    """
    Return the date of the n-th given weekday in a month.
    month: 1-12, weekday: 0=Monday..6=Sunday, n>=1
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
@@ -150,52 +152,96 @@ st.markdown(
    """
    <style>
    .main .block-container {
        max-width: 380px;
        padding: 1.5rem 1.25rem;
        position: fixed;
        top: 1rem;
        right: 1rem;
        background: #ffffff;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.16);
        border-radius: 12px;
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

business_days_to_add = 30  # fixed per your requirement

today = dt.date.today()
with st.form(key="calculator_form"):
    start_date = st.date_input(
        "Start date (MM/DD/YYYY)",
        value=today,
        format="MM/DD/YYYY",
    )
    submitted = st.form_submit_button("Calculate", type="primary")
st.markdown(
    """
    <script>
    const root = window.parent.document;
    const dateInput = root.querySelector('input[aria-label="Start date (MM/DD/YYYY)"]');
    const calcButton = Array.from(root.querySelectorAll('button')).find((btn) => btn.innerText.trim() === 'Calculate');
    if (dateInput && calcButton && !dateInput.dataset.enterSubmitBound) {
        dateInput.dataset.enterSubmitBound = 'true';
        dateInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                calcButton.click();
            }
        });
    }
    </script>
    """,
    unsafe_allow_html=True,
)

if submitted:
    business_dates = calculate_business_dates(start_date, business_days_to_add)

    if len(business_dates) < business_days_to_add:
        st.error("Could not compute the full range of business days.")
    else:
        final_date = business_dates[-1]
        formatted_final = final_date.strftime("%m/%d/%Y")

        st.subheader("Result")
        result_template = Template(
            """
            <div style="display: flex; align-items: center; gap: 10px; margin-top: 0.25rem;">
                <span style="font-size: 32px; font-weight: 700; letter-spacing: 0.5px;">${formatted_final}</span>
                <button id="copy-date-btn" style="border: none; background: transparent; cursor: pointer; font-size: 20px;" aria-label="Copy result date">📋</button>
            </div>
            <script>
            const copyBtn = window.parent.document.getElementById('copy-date-btn');
            if (copyBtn && !copyBtn.dataset.boundCopy) {
                copyBtn.dataset.boundCopy = 'true';
                copyBtn.addEventListener('click', async () => {
                    try {
                        await navigator.clipboard.writeText(${json_formatted});
                        copyBtn.textContent = '✅';
                        setTimeout(() => copyBtn.textContent = '📋', 1200);
                    } catch (err) {
                        console.error('Copy failed', err);
                    }
                });
            }
            </script>
            """
        )

        result_html = result_template.substitute(
            formatted_final=formatted_final,
            json_formatted=json.dumps(formatted_final),
        )

        st.markdown(result_html, unsafe_allow_html=True)
