from __future__ import annotations

import notion_client  # type: ignore[import-not-found]

from ..utils.environment import Environment


def add_item_to_database(data: dict) -> None:
    """Adds a new page (row) to the specified Notion database.

    Expected keys: company_name, application_date, role
    Map these to Notion properties named exactly:
    - Company Name (title)
    - Application Date (date)
    - Role (rich_text or title)
    """
    # if not all(
    #     k in data and data[k] for k in ["company_name", "application_date", "role"]
    # ):
    #     print("Extracted data is missing required keys. Skipping Notion entry.")
    #     return

    try:
        notion = notion_client.Client(auth=str(Environment.get_notion_api_key()))

        # Property names and types must match your Notion DB schema
        new_page = {
            "Company Name": {
                "title": [{"text": {"content": str(data["company_name"])}}]
            },
            "Application Date": {"date": {"start": str(data["application_date"])}},
            "Role": {"rich_text": [{"text": {"content": str(data["role"])}}]},
        }

        notion.pages.create(
            parent={"database_id": str(Environment.get_notion_db_id())},
            properties=new_page,
        )
        print(
            "Successfully added '"
            + str(data["company_name"])
            + "' application for role '"
            + str(data["role"])
            + "' to Notion."
        )

    except notion_client.errors.APIResponseError as e:
        print(f"Error communicating with Notion API: {e}")
    except Exception as e:
        print(f"An unexpected error occurred with Notion: {e}")
