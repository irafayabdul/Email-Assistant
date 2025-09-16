from __future__ import annotations

import time

from .services import gmail_service
from .services import llm_service
from .services import notion_service
from .utils.environment import Environment


def main() -> None:
    """The main function to orchestrate the email processing workflow."""
    print("--- Starting new workflow cycle ---")

    # 1. Authenticate and get Gmail service
    service = gmail_service.get_gmail_service()
    if not service:
        print("Failed to get Gmail service. Exiting cycle.")
        return

    # 2. Find emails newly labeled with the specified label since last poll
    gmail_label = str(Environment.get_gmail_label())
    print(f"Polling for newly labeled emails with label: '{gmail_label}'")
    label_id = gmail_service.get_label_id(service, gmail_label)
    if not label_id:
        print("Target label not found; skipping this cycle.")
        return
    newly_labeled_ids = gmail_service.get_newly_labeled_message_ids(service, label_id)

    if not newly_labeled_ids:
        print("No newly labeled emails found.")
        return

    print(f"Found {len(newly_labeled_ids)} newly labeled email(s).")

    # 3. Process each email
    for msg_id in newly_labeled_ids:
        email_details = gmail_service.get_email_details(service, msg_id)

        if email_details:
            # 4. Use LLM to extract information
            print(
                f"\nProcessing email from: {email_details['sender']} \
                                         - {email_details['subject']}"
            )
            # Include received date to help the model extract the correct date
            full_content = (
                f"Subject: {email_details['subject']}\n"
                f"From: {email_details['sender']}\n"
                f"Received Date: {email_details['received_date']}\n\n"
                f"{email_details['body']}"
            )
            extracted_data = llm_service.extract_info_from_email(full_content)

            if extracted_data:
                # 5. Add extracted data to Notion
                notion_service.add_item_to_database(extracted_data)


if __name__ == "__main__":
    print("Starting Gmail to Notion Automation Service.")
    polling_interval = int(Environment.get_gmail_polling_interval() or 300)
    print(f"Polling every {polling_interval} seconds. Press Ctrl+C to stop.")

    # This creates the long-running service loop
    try:
        while True:
            main()
            print(f"--- Cycle complete. Waiting for {polling_interval} seconds... ---")
            time.sleep(polling_interval)
    except KeyboardInterrupt:
        print("\n Service stopped by user.")
