# src/email_parser.py
import base64
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from email.header import decode_header
from bs4 import BeautifulSoup  # We'll add this to requirements later
from datetime import datetime
import dateutil.parser

from config import SHEET_DATE_FORMAT  # "%Y-%m-%d %H:%M:%S"


def decode_subject(subject_header):
    """Decode subject that may have encoded words (UTF-8, etc.)"""
    if not subject_header:
        return "(No Subject)"
    decoded = decode_header(subject_header)[0]
    subject, encoding = decoded
    if isinstance(subject, bytes):
        try:
            return subject.decode(encoding or "utf-8", errors="replace")
        except:
            return subject.decode("utf-8", errors="replace")
    return subject


def get_from_address(headers):
    """Extract clean sender email from headers"""
    for header in headers:
        if header["name"].lower() == "from":
            value = header["value"]
            # Simple extraction: take the email part (handles "Name <email@domain.com>")
            if "<" in value and ">" in value:
                return value.split("<")[1].split(">")[0].strip()
            return value.strip()
    return "Unknown Sender"


def get_date(headers):
    """Parse received date and format for sheet"""
    for header in headers:
        if header["name"].lower() == "date":
            try:
                dt = dateutil.parser.parse(header["value"])
                return dt.strftime(SHEET_DATE_FORMAT)
            except:
                pass
    return datetime.utcnow().strftime(SHEET_DATE_FORMAT)  # fallback


def get_plain_text_body(payload):
    """Extract plain text body, preferring text/plain over html"""
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            elif part["mimeType"] == "text/html":
                # Fallback to HTML → plain text
                data = part["body"].get("data")
                if data:
                    html = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    soup = BeautifulSoup(html, "html.parser")
                    return soup.get_text(separator="\n", strip=True)
        # Recursive for nested multipart
        for part in payload["parts"]:
            if "parts" in part["payload"]:
                text = get_plain_text_body(part["payload"])
                if text:
                    return text
    elif "data" in payload["body"]:
        data = payload["body"]["data"]
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    
    return "(No readable body content)"


def parse_email(message):
    """
    Main function: Parse raw Gmail message → dict with From, Subject, Date, Content
    """
    headers = message["payload"]["headers"]
    
    from_email = get_from_address(headers)
    subject = decode_subject(next((h["value"] for h in headers if h["name"].lower() == "subject"), None))
    date_str = get_date(headers)
    content = get_plain_text_body(message["payload"])
    
    return {
        "From": from_email,
        "Subject": subject,
        "Date": date_str,
        "Content": content
    }