from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any
from typing import cast

import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"


def _validate_iso_date(value: str | None) -> str | None:
    """Accept only strict YYYY-MM-DD dates; reject everything else.

    - Requires exact regex match
    - Also validates the calendar date via datetime.strptime
    """
    if not value:
        return None
    candidate = value.strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate):
        return None
    try:
        dt = datetime.strptime(candidate, "%Y-%m-%d")
        return dt.date().isoformat()
    except Exception:
        return None


def _build_prompt(email_content: str) -> str:
    """Few-shot + CoT style prompt. Model reasons internally; output is strict JSON."""
    return f"""
You are a careful information extraction assistant. Think step by step to identify the
company name, the application date, and the role, but output ONLY a single JSON object
with keys exactly: company_name, application_date, role.

Rules for application_date:
- Prefer the provided "Received Date:" line if present.
- Otherwise, extract the most plausible application date from the email text.
- The value MUST be formatted as YYYY-MM-DD (ISO date) with no extra characters.
- If you cannot find a date, return 1999-01-01.

Examples:
Input:
Subject: Application to Foo Corp\nReceived Date: 2025-09-09\nBody: Thank you!
Output:
{{"company_name": "Foo Corp", "application_date": "2025-09-09", "role": ""}}

Input:
Subject: Re: Interview with Bar Inc\nBody: Your application for Data Scientist on Sep 8
, 2025 was received.
Output:
{{"company_name": "Bar Inc", "application_date": "2025-09-08", "role": "Data Scientist"
}}

Input:
Subject: Thanks\nBody: No clear date
Output:
{{"company_name": "", "application_date": "1999-01-01", "role": ""}}

Email content:
---
{email_content}
---

Return ONLY the JSON object.
JSON Output:
"""


def extract_info_from_email(email_content: str) -> dict | None:
    """Sends email content to a local LLM to extract structured data with
    few-shot prompting, light CoT, and basic self-consistency fallback.
    """

    def call_model(prompt: str) -> dict | None:
        response_data: dict | None = None
        try:
            payload = {
                "model": "qwen3:4b",
                "prompt": prompt,
                "format": "json",
                "stream": False,
            }

            response = requests.post(OLLAMA_API_URL, json=payload)
            response.raise_for_status()
            response_data = response.json()
            json_string = response_data.get("response", "{}")
            result = json.loads(json_string)
            return cast(dict[str, Any], result) if isinstance(result, dict) else None
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with Ollama: {e}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from LLM response: {e}")
            if response_data is not None:
                print(f"Raw response was: {response_data.get('response')}")
        return None

    prompt = _build_prompt(email_content)

    # Try multiple times for self-consistency (pick the first with a valid date)
    attempts = 5
    best: dict | None = None
    for _ in range(attempts):
        extracted_data = call_model(prompt)
        if not extracted_data:
            continue
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

        # Post-validate date
        date_norm = _validate_iso_date(normalized.get("application_date"))
        if date_norm is not None:
            normalized["application_date"] = date_norm
            best = normalized
            break
        else:
            # force default if later attempts fail too
            best = normalized

    if best is None:
        return None

    if not best.get("application_date"):
        best["application_date"] = "1999-01-01"

    print(f"LLM extracted data: {best}")
    return best
