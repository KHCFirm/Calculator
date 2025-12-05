# 30 Business Day Calculator (Streamlit)

This is a small Streamlit app that calculates the date that is **30 business days** after a given start date.

- The **start date counts as Day 1**
- Weekends are skipped
- U.S. federal holidays are skipped (with observed rules when they fall on weekends)
- The result is displayed in **MM/DD/YYYY** format

## Setup

1. Create and activate a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate    # macOS/Linux
   .venv\Scripts\activate       # Windows
