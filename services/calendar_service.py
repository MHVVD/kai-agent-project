# In: services/calendar_service.py
import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

def get_calendar_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    service = build("calendar", "v3", credentials=creds)
    return service

def schedule_event(summary: str, duration_hours: int = 1, recurrence_rule: str = None):
    service = get_calendar_service()
    now = datetime.datetime.utcnow()
    start_time = now.isoformat() + "Z"
    end_time = (now + datetime.timedelta(hours=duration_hours)).isoformat() + "Z"
    event = {
        'summary': summary, 'description': 'Scheduled by your KAI Agent.',
        'start': {'dateTime': start_time, 'timeZone': 'UTC'},
        'end': {'dateTime': end_time, 'timeZone': 'UTC'},
    }
    if recurrence_rule:
        event['recurrence'] = [recurrence_rule]
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    print(f"Event created: {created_event.get('htmlLink')}")
    return "Event scheduled successfully."