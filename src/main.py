# src/main.py
import sys
import os

# Fix sys.path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from datetime import datetime
import dateutil.parser

from config import SCOPES, SHEET_DATE_FORMAT
from src.gmail_service import get_gmail_service, load_last_timestamp, save_last_timestamp, get_unread_messages_since_last
from src.sheets_service import get_sheets_service, ensure_headers, is_duplicate, append_email_row
from src.email_parser import parse_email

def mark_as_read(service, message_id):
    """Mark email as read (remove UNREAD label)"""
    try:
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()
        print(f"Marked as read: {message_id}")
    except Exception as e:
        print(f"Failed to mark as read: {e}")

def main():
    print("Starting Gmail to Sheets logger...")

    # Services
    gmail_service = get_gmail_service()
    sheets_service = get_sheets_service()

    # Ensure sheet headers
    ensure_headers(sheets_service)

    # Fetch new unread emails
    messages = get_unread_messages_since_last(gmail_service)
    if not messages:
        print("No new unread emails found.")
        return

    processed_dates = []  # To track max date for state update

    for msg in messages:
        parsed = parse_email(msg)
        from_email = parsed["From"]
        subject = parsed["Subject"]
        date_str = parsed["Date"]
        content = parsed["Content"]

        # Optional duplicate check
        if is_duplicate(sheets_service, from_email, subject, date_str):
            print(f"Skipping duplicate: {subject}")
            # Still mark as read to clean inbox
            mark_as_read(gmail_service, msg["id"])
            continue

        # Append to sheet
        success = append_email_row(sheets_service, from_email, subject, date_str, content)
        if success:
            mark_as_read(gmail_service, msg["id"])
            processed_dates.append(dateutil.parser.parse(date_str))  # for max date

    # Update state with the latest processed date
    if processed_dates:
        latest_dt = max(processed_dates)
        latest_str = latest_dt.strftime(SHEET_DATE_FORMAT)
        save_last_timestamp(latest_str)
        print(f"Updated last processed: {latest_str}")

    print("Processing complete!")

if __name__ == "__main__":
    main()