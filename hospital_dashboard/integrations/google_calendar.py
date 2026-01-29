import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarService:
    def __init__(self):
        self.service = self._create_service()

    # -------------------------------
    # CREATE SERVICE
    # -------------------------------
    def _create_service(self):
        try:
            service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

            if not service_account_json:
                print("❌ GOOGLE_SERVICE_ACCOUNT_JSON not found")
                return None

            info = json.loads(service_account_json)

            credentials = service_account.Credentials.from_service_account_info(
                info,
                scopes=SCOPES
            )

            service = build("calendar", "v3", credentials=credentials)
            print("✅ Google Calendar service created successfully")
            return service

        except Exception as e:
            print("❌ Failed to create Google Calendar service:", e)
            return None

    # -------------------------------
    # CREATE EVENT
    # -------------------------------
    def create_event(self, summary, description, start_time, end_time, attendees):

        if not self.service:
            print("❌ Google service is None")
            return None

        event = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "Asia/Kolkata",
            }
        }

        try:
            created_event = self.service.events().insert(
                calendarId="primary",
                body=event
            ).execute()

            print("🎯 EVENT CREATED")
            print("ID:", created_event.get("id"))
            print("LINK:", created_event.get("htmlLink"))

            return created_event

        except Exception as e:
            print("🔥 GOOGLE API ERROR:", e)
            return None

    # -------------------------------
    # DELETE EVENT
    # -------------------------------
    def delete_event(self, event_id):

        if not self.service:
            return False

        try:
            self.service.events().delete(
                calendarId="primary",
                eventId=event_id
            ).execute()
            return True

        except Exception as e:
            print("🔥 DELETE ERROR:", e)
            return False
