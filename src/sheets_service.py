# src/sheets_service.py
import sys
import os

# Fix for running scripts directly from src/ folder
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import (
    CREDENTIALS_FILE, TOKEN_FILE, SCOPES,
    SPREADSHEET_ID, SHEET_NAME, HEADER_ROW
)

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def get_sheets_service():
    """Returns authenticated Google Sheets v4 service"""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)


def ensure_headers(service):
    """Adds header row if missing"""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1:D1"
        ).execute()

        if not result.get("values") or result.get("values")[0] != HEADER_ROW:
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A1",
                valueInputOption="RAW",
                body={"values": [HEADER_ROW]}
            ).execute()
            print("Headers written.")
        # else: silent (already good)

    except HttpError as e:
        print(f"Header check/update failed: {e}")
        if "not found" in str(e).lower():
            print("→ Check that SPREADSHEET_ID and SHEET_NAME in config.py are correct!")
        raise


def is_duplicate(service, from_email, subject, date_str, lookback=100):
    """Quick duplicate check on recent rows"""
    try:
        # Optimistic: try recent rows first
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A2:D{lookback+10}"  # A little buffer
        ).execute()

        rows = result.get("values", [])
        if not rows:
            return False

        for row in rows:
            if len(row) < 3:
                continue
            if (row[0] == from_email and 
                row[1] == subject and 
                row[2] == date_str):
                print(f"Duplicate skipped: {subject} | {from_email} | {date_str}")
                return True

        return False

    except HttpError as e:
        print(f"Duplicate check error: {e} → proceeding anyway")
        return False  # fail-safe: allow insert


def append_email_row(service, from_email, subject, date_str, content):
    """Append single email row"""
    MAX_CONTENT = 30000
    if len(content) > MAX_CONTENT:
        content = content[:MAX_CONTENT] + "… [truncated]"

    try:
        values = [[from_email, subject, date_str, content]]

        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:D",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": values}
        ).execute()

        print(f"→ Added: {date_str} | {from_email} | {subject}")
        return True

    except HttpError as e:
        print(f"Append error: {e}")
        return False