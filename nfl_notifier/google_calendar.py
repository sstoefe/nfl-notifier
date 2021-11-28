import pickle

from googleapiclient.discovery import build, Resource
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pathlib import Path
from typing import Dict


def get_calendar_service() -> Resource:
    """Create the Google Calendar service with permissions to access calendar events.

    Returns:
        Resource: The Google Calendar service
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if Path("token.pickle").exists():
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", "https://www.googleapis.com/auth/calendar.events"
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds)
    return service


def create_event(
    summary: str,
    description: str,
    starttime: str,
    endtime: str,
    timezone: str = "Europe/Berlin",
) -> Dict:
    """Create a Google Calendar event with the given information.

    Args:
        summary (str): title of the event
        description (str): description of the event
        starttime (str): starttime of the event
        endtime (str): endtime of the event
        timezone (str, optional): timezone of the event. Defaults to "Europe/Berlin".

    Returns:
        Dict: status of newly created event
    """
    service = get_calendar_service()

    calendar_event = {
        "summary": summary,
        "description": description,
        "start": {
            "dateTime": starttime,
            "timeZone": timezone,
        },
        "end": {
            "dateTime": endtime,
            "timeZone": timezone,
        },
    }

    return service.events().insert(calendarId="primary", body=calendar_event).execute()
