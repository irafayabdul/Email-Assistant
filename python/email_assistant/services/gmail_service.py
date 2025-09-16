from __future__ import annotations

import base64
import json
import os.path
from email.utils import parsedate_to_datetime
from typing import Any
from typing import cast
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

from google.auth.transport.requests import Request  # type: ignore[import-not-found]
from google.oauth2.credentials import Credentials  # type: ignore[import-not-found]
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore[import-not-found]
from googleapiclient.discovery import build  # type: ignore[import-not-found]
from googleapiclient.errors import HttpError  # type: ignore[import-not-found]


# The file token.json stores the user's access and refresh tokens.
# It is created automatically when the authorization flow completes for the first time.
TOKEN_PATH = "token.json"
CREDS_PATH = "credentials.json"
STATE_PATH = "gmail_state.json"


def get_gmail_service() -> Any:
    """Authenticates with Google and returns a Gmail service object."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(
            TOKEN_PATH,
            [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.modify",
            ],
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDS_PATH,
                [
                    "https://www.googleapis.com/auth/gmail.readonly",
                    "https://www.googleapis.com/auth/gmail.modify",
                ],
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _load_state() -> Dict:
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r") as f:
                return cast(Dict[str, Any], json.load(f))
        except Exception:
            return {}
    return {}


def _save_state(state: Dict) -> None:
    try:
        with open(STATE_PATH, "w") as f:
            json.dump(state, f)
    except Exception as e:
        print(f"Failed to persist Gmail state: {e}")


def _get_current_history_id(service: Any) -> Optional[str]:
    try:
        profile = cast(
            Dict[str, Any], service.users().getProfile(userId="me").execute()
        )
        return str(profile.get("historyId")) if profile.get("historyId") else None
    except HttpError as error:
        print(f"Unable to get current historyId: {error}")
        return None


def get_label_id(service: Any, label_name: str) -> Optional[str]:
    try:
        labels = cast(
            List[Dict[str, Any]],
            service.users().labels().list(userId="me").execute().get("labels", []),
        )
        for label in labels:
            if label.get("name") == label_name:
                return label.get("id")
        print(f"Label '{label_name}' not found in Gmail account.")
        return None
    except HttpError as error:
        print(f"Error fetching labels: {error}")
        return None


def get_newly_labeled_message_ids(service: Any, label_id: str) -> List[str]:
    """Return message ids that were newly labeled with the given label since last poll.

    Uses Gmail History API with historyTypes=labelAdded and persists last historyId.
    On first run (no saved state), initializes last_history_id and returns no messages.
    """
    state = _load_state()
    last_history_id = state.get("last_history_id")

    if last_history_id is None:
        current_history_id = _get_current_history_id(service)
        if current_history_id is None:
            return []
        state["last_history_id"] = current_history_id
        _save_state(state)
        return []

    collected_ids: Set[str] = set()
    page_token: Optional[str] = None
    max_history_id = int(last_history_id)

    try:
        while True:
            req = (
                service.users()
                .history()
                .list(
                    userId="me",
                    startHistoryId=last_history_id,
                    historyTypes="labelAdded",
                    labelId=label_id,
                    pageToken=page_token,
                )
            )
            resp = cast(Dict[str, Any], req.execute())

            history = cast(List[Dict[str, Any]], resp.get("history", []))
            for h in history:
                hid = int(h.get("id", last_history_id))
                if hid > max_history_id:
                    max_history_id = hid
                for event in h.get("labelsAdded", []):
                    # event: {message: {...}, labelIds: [...]}
                    if label_id in event.get("labelIds", []):
                        message = event.get("message", {})
                        if "id" in message:
                            collected_ids.add(message["id"])

            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        # Update last_history_id to max seen
        state["last_history_id"] = str(max_history_id)
        _save_state(state)
    except HttpError as error:
        print(f"Error fetching Gmail history: {error}")

    return list(collected_ids)


def get_email_details(service: Any, message_id: str) -> Optional[Dict[str, str]]:
    """Gets the content of a single email."""
    try:
        msg = cast(
            Dict[str, Any],
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute(),
        )
        payload = cast(Dict[str, Any], msg["payload"])
        headers = cast(List[Dict[str, Any]], payload["headers"])

        subject = next(h["value"] for h in headers if h["name"].lower() == "subject")
        sender = next(h["value"] for h in headers if h["name"].lower() == "from")
        date_header = next(h["value"] for h in headers if h["name"].lower() == "date")
        received_dt = parsedate_to_datetime(date_header)
        received_iso = received_dt.isoformat()

        body = ""
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    encoded_body = part["body"].get("data", "")
                    body = base64.urlsafe_b64decode(encoded_body).decode("utf-8")
                    break
        else:
            encoded_body = payload["body"].get("data", "")
            body = base64.urlsafe_b64decode(encoded_body).decode("utf-8")

        return {
            "id": message_id,
            "sender": sender,
            "subject": subject,
            "received_date": received_iso,
            "body": body,
        }
    except Exception as e:
        print(f"Could not parse email {message_id}: {e}")
        return None
