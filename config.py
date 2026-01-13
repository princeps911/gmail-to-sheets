# config.py  (place in project ROOT, NOT inside src/)
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CREDENTIALS_DIR = os.path.join(BASE_DIR, "credentials")
CREDENTIALS_FILE = os.path.join(CREDENTIALS_DIR, "credentials.json")
TOKEN_FILE = os.path.join(CREDENTIALS_DIR, "token.json")
STATE_FILE = os.path.join(CREDENTIALS_DIR, "state.json")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets"
]

# ← CHANGE THESE TWO ↓
SPREADSHEET_ID = "1elWxoP2y1iJ8Zwo1LTIdzAFDbUegxmRvmTLasaJCIgs"   # ← required!
SHEET_NAME = "Emails"

HEADER_ROW = ["From", "Subject", "Date", "Content"]
SHEET_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
GMAIL_QUERY_BASE = "in:inbox is:unread"