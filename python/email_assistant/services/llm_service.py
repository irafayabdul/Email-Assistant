from __future__ import annotations

import json

import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"


def extract_info_from_email(email_content: str) -> dict | None:
    """Sends email content to a local LLM to extract structured data.

    Expected output keys:
    - company_name: Name of the company applied to
    - application_date: ISO date string when the email was received
    - role: Job title applied for
    """

    prompt = f"""
    You extract structured job application details from emails.

    From the email below, extract these fields:
    - company_name: the company the user applied to
    - application_date: the date the email was received. Return the provided Received
                        Date if available else Return the date found anywhere in the
                        email in this format YYYY-MM-DD. Make sure to return the date
                        in the correct format only, remove any trailing characters and
                        spaces in the characters of date to make it a valid date in the
                        format YYYY-MM-DD, if no date found Return 2000-01-01.
    - role: the job title applied for

    Return ONLY JSON with these exact keys: company_name, application_date, role.

    Email content:
    ---
    {email_content}
    ---

    JSON Output:
    """

    try:
        payload = {
            "model": "qwen3:4b",  # Or another model you have pulled
            "prompt": prompt,
            "format": "json",
            "stream": False,
        }

        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()

        response_data = response.json()
        json_string = response_data.get("response", "{}")

        extracted_data = json.loads(json_string)

        # Normalize keys if model returns variants
        normalized = {
            "company_name": extracted_data.get("company_name")
            or extracted_data.get("company")
            or extracted_data.get("Company Name"),
            "application_date": extracted_data.get("application_date")
            or extracted_data.get("date")
            or extracted_data.get("Application Date"),
            "role": extracted_data.get("role")
            or extracted_data.get("position")
            or extracted_data.get("Role"),
        }

        print(f"LLM extracted data: {normalized}")
        return normalized

    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from LLM response: {e}")
        print(f"Raw response was: {response_data.get('response')}")

    return None
