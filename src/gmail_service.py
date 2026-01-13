# src/gmail_service.py
import sys
import os
import json
from datetime import datetime
from dateutil import parser

# Fix sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import config constants (this line was probably missing)
from config import (
    SCOPES,
    CREDENTIALS_FILE,
    TOKEN_FILE,
    STATE_FILE,          
    GMAIL_QUERY_BASE
)

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def get_gmail_service():
    """Build and return authenticated Gmail service"""
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

    return build("gmail", "v1", credentials=creds)


def load_last_timestamp() -> str | None:
    """Load last processed timestamp (RFC3339)"""
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            return data.get("last_processed_rfc3339")
    except Exception:
        return None


def save_last_timestamp(timestamp_str: str):
    """Save latest timestamp to state file"""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"last_processed_rfc3339": timestamp_str}, f, indent=2)


def get_timestamp_after_filter(last_ts: str | None) -> str:
    """Build 'after:' part for Gmail query"""
    if not last_ts:
        # First run → last 7 days to be safe (adjust as needed)
        seven_days_ago = int((datetime.utcnow().timestamp() - 7*86400))
        return f"after:{seven_days_ago}"
    
    # Convert to unix timestamp for safety
    dt = parser.parse(last_ts)
    unix_ts = int(dt.timestamp())
    return f"after:{unix_ts}"
def get_unread_messages_since_last(service):
    """
    Fetch list of unread inbox emails since last processed timestamp.
    
    Returns: list of raw message dicts (from API) or empty list if none.
    """
    last_ts = load_last_timestamp()
    after_filter = get_timestamp_after_filter(last_ts)
    query = f"{GMAIL_QUERY_BASE} {after_filter}"
    
    print(f"Fetching emails with query: '{query}'")  # For debugging
    
    messages = []
    page_token = None
    
    try:
        while True:
            response = service.users().messages().list(
                userId="me",
                q=query,
                pageToken=page_token
            ).execute()
            
            if "messages" in response:
                msg_ids = [msg["id"] for msg in response["messages"]]
                
                for msg_id in msg_ids:
                    msg = service.users().messages().get(
                        userId="me",
                        id=msg_id,
                        format="full"  # Gets headers + payload (body)
                    ).execute()
                    messages.append(msg)
            
            page_token = response.get("nextPageToken")
            if not page_token:
                break
    
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []
    
    print(f"Found {len(messages)} new unread emails.")
    return messages