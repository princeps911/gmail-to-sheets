# Gmail to Google Sheets Logger

A Python automation that reads **unread inbox emails** from your Gmail account using the Gmail API and automatically logs them into a Google Sheet.

Features:
- Fetches only new unread emails since the last run
- Extracts: **From**, **Subject**, **Date**, **Content** (plain text)
- Appends each email as a new row in Google Sheets
- Marks processed emails as read
- Prevents re-processing using timestamp-based state persistence
- Secure OAuth 2.0 authentication (no app passwords)

## Architecture Overview
Gmail API
↓
gmail_service.py
↓ (new unread messages)
email_parser.py → parsed data
↓
sheets_service.py → append to Google Sheet
↓
main.py
(orchestrates everything)
↑
state.json
(stores last processed timestamp)

Gmail → [fetch unread since last] → Parse → Check duplicate → Append to Sheet → Mark Read → Update state

## Setup Instructions (Step-by-Step)

1. **Clone the repository**
   ```bash
   git clone https://github.com/princeps911/gmail-to-sheets.git
   cd gmail-to-sheets

Create & activate virtual environment (recommended)Bashpython -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
Install dependenciesBashpip install -r requirements.txt
Enable Google APIs & get credentials
Go to https://console.cloud.google.com/apis/dashboard
Create new project
Enable Gmail API and Google Sheets API
Credentials → Create Credentials → OAuth client ID → Desktop app
Download JSON → rename to credentials.json
Move it to credentials/credentials.json

Configure the sheet
Create a new Google Sheet
Copy Spreadsheet ID from URL
Paste it into config.py:PythonSPREADSHEET_ID = "your-spreadsheet-id-here"

First runBashpython src/main.py→ Browser will open for Google login & permission grant
→ First time shows "App isn't verified" warning → click Advanced → Go to [app name] (unsafe)
→ Emails will be processed & added to sheet

How State Persistence Works

We store the last processed email timestamp (RFC3339 format) in credentials/state.json
On each run → only fetch emails received after this timestamp
After successful processing → update state with the most recent date among processed emails
Why timestamp instead of historyId?
→ Simpler, reliable for personal use, sufficient for inbox-only unread emails, less API complexity

Duplicate Prevention Logic

Primary: Fetch only is:unread + after:last_timestamp
Secondary: Mark email as read after successful append
Tertiary (safety): Check recent sheet rows for exact From + Subject + Date match

Challenges Faced & Solutions

OAuth "App not verified" error → Set app to Testing mode + add yourself as test user in Google Cloud Console
ModuleNotFoundError for config → Added sys.path fix to make imports work when running from src/ folder
Date parsing inconsistencies → Used dateutil.parser for robust email date handling
Windows path issues → Used absolute paths via os.path and careful activation of venv

Limitations

Only processes plain text bodies (HTML converted to text, no images/attachments)
Very large email bodies (>30k chars) are truncated
No support for spam/trash/deleted emails
Rate limited by Google APIs (usually not an issue for personal use)
Requires your computer to run the script (no cloud hosting in current version)
First run fetches last 7 days (fallback) if no state exists