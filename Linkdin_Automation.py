import re
import time
import json
import csv
import os
import requests
from playwright.sync_api import sync_playwright

# Load config.json
with open("config.json", "r") as f:
    config = json.load(f)

with open("resume.txt", "r", encoding="utf-8") as file:
    resume_text = file.read()

def is_valid_llm_answer(answer):
    if not answer or not answer.strip():
        return False
    lowered = answer.strip().lower()
    bad_phrases = [
        "the resume does not",
        "not mentioned",
        "not found",
        "no experience",
        "unable to find",
        "based on the provided resume"
    ]
    return not any(phrase in lowered for phrase in bad_phrases)

LINKEDIN_USERNAME = config["LINKEDIN_USERNAME"]
LINKEDIN_PASSWORD = config["LINKEDIN_PASSWORD"]
RESUME_PATH = config["resume_path"]
TARGET_JOB_TITLE = config["target_job_title"]
TARGET_LOCATION = config["target_location"]
LOG_FILE_PATH = config["log_file_path"]
OPENWEBUI_API = config["OPENWEBUI_API_URL"]
OPENWEBUI_MODEL = config["OPENWEBUI_MODEL"]
MAX_JOBS_PER_RUN = config.get("max_jobs_per_run", 5)
api_token = config["OPENWEBUI_API_KEY"]

USER_NAME = "Manisha Walunj"  # Change as needed
MODEL = "gemma"

def upload_resume_get_file_id(RESUME_PATH):
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json"
    }

    with open(RESUME_PATH, "rb") as f:
        files = {"file": f}
        resp = requests.post(f"{OPENWEBUI_API}/api/v1/files/", headers=headers, files=files)
        resp.raise_for_status()
        file_id = resp.json()["id"]
        print(f"Uploaded file. File ID: {file_id}")
        return file_id  # Return it!

def css_escape(s):
    return re.sub(r'([!"#$%&\'()*+,./:;<=>?@[\\\]^`{|}~])', r'\\\1', s)

def normalize_answer(text, question=""):
    text = text.strip().lower()

    # If the question is a Yes/No style
    if any(x in question.lower() for x in
           ["agree", "policy", "authorized", "permission", "consent", "privacy", "eligible"]):
        # if text in ["yes", "y", "yeah", "1", "true", "2"]:
        #     return "Yes"
        # elif text in ["no", "n", "nope", "0", "false"]:
        #     return "No"
        if text in ["yes", "y", "yeah", "1", "true", "2"]:
            return "Yes"
        elif text in ["no", "n", "nope", "0", "false"]:
            return "No"

    if "year" in question.lower():
        import re
        # Extract a 4-digit year or 2-digit and expand
        year_match = re.search(r"\b(20\d{2}|\d{2})\b", text)
        if year_match:
            year = year_match.group()
            if len(year) == 2:
                year = "20" + year  # Convert "23" → "2023"
            return year

    return text.capitalize()
    # return text.strip().capitalize()

def log_application_data(job_title, company_name, location, description):
    log_file = 'application_log.csv'
    file_exists = os.path.isfile(log_file)

    with open(log_file, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow([
                'Job Title',
                'Company Name',
                'Location',
                'Job Description'
            ])

        writer.writerow([
            job_title,
            company_name,
            location,
            description
        ])

def get_answer_from_llm(question, file_id):
    chat_headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "model": OPENWEBUI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": (
                    f"You are a helpful assistant. Answer the following job application question "
                    f"based only on the resume content in the uploaded file.\n\n"
                    f"If the question asks about years of experience with a specific skill or technology "
                    f"(e.g., Angular, Node.js), extract that number from the resume if present. "
                    f"If it's not mentioned or you're unsure, do not answer at all. Leave it blank.\n\n"
                    f"If the question is about eligibility (Yes/No), answer only Yes or No.\n"
                    f"If unsure, answer 0 for years or No for eligibility.\n\n"
                    f"If it's a Yes/No question, answer only Yes or No. If unsure, return nothing.\n"
                    f"If the question presents multiple choices (checkbox or radio), answer with the most relevant option exactly as it appears (e.g., 'Beginner', 'PostgreSQL'). Do not explain.\n"
                    f"Resume:\n{resume_text}\n\n"
                    f"Question: {question}"
                )
            }
        ],
        "files": [{"type": "file", "id": file_id}]
    }

    response = requests.post(
        f"{OPENWEBUI_API}/api/chat/completions",
        headers=chat_headers,
        json=payload
    )

    response.raise_for_status()
    answer = response.json()['choices'][0]['message']['content']

    if not is_valid_llm_answer(answer):
        return None  # tell caller to skip job if LLM can't answer

    # return answer.strip()
    import re
    cleaned = answer.strip()
    cleaned = re.sub(r"^\s*(\d+\.)\s*", "", cleaned)  # remove "1. ", "2. ", etc.
    cleaned = re.sub(r"^\s*[-•]\s*", "", cleaned)  # remove "-", "•" bullets
    return cleaned

def login_to_linkedin(page):
    page.goto("https://www.linkedin.com/login")
    page.fill('input#username', LINKEDIN_USERNAME)
    page.fill('input#password', LINKEDIN_PASSWORD)
    page.click('button[type="submit"]')
    try:
        page.wait_for_url("https://www.linkedin.com/feed/", timeout=60000)
        print("Logged in Successfully")
    except:
        page.screenshot(path="login_failed.png")
        print("Login failed. Check credentials or captcha requirement.")
        page.wait_for_timeout(10000)

def is_yes_no_option(text):
    return text.strip().lower() in ["yes", "no", "maybe"]

def search_jobs(page, job_title=TARGET_JOB_TITLE, job_location=TARGET_LOCATION):
    page.goto("https://www.linkedin.com/jobs/")
    if job_title:
        try:
            title_input = page.locator('//input[@aria-label="Search by title, skill, or company"]').first
            title_input.wait_for(state="visible", timeout=20000)
            title_input.click()
            title_input.fill(job_title)
            print("Entered Job Title")
        except Exception as e:
            print("Error entering job title:", e)
    if job_location:
        try:
            location_input = page.locator('//input[@aria-label="City, state, or zip code"]').first
            location_input.wait_for(state="visible", timeout=15000)
            location_input.click()
            location_input.press("Control+A")
            location_input.press("Backspace")
            location_input.fill(job_location)
            page.wait_for_selector("ul[role='listbox'] li", timeout=5000)
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)
            print("Entered Job Location")
        except Exception as e:
            print("Error entering job location:", e)

def select_custom_dropdown(field, answer):
    try:
        field.click()
        time.sleep(0.5)  # Wait for dropdown to render
        dropdown_panel = field.page.locator("div[role='listbox'], ul[role='listbox'], div[aria-expanded='true']")
        option = dropdown_panel.get_by_text(answer, exact=True)
        if not option.is_visible():
            option = dropdown_panel.get_by_text(answer)
        option.click()
        print(f"Custom dropdown option selected: {answer}")
    except Exception as e:
        print(f"Failed to select from custom dropdown: {e}")

def extract_and_fill_form_fields_across_steps(page, file_id):
    print("\nExtracting and filling form fields from all steps:")
    seen = set()

    def fill_field(field, label_text):
        try:
            if not field:
                print(f"No field found for label: {label_text}")
                return
            tag = field.evaluate("el => el.tagName.toLowerCase()")
            input_type = field.get_attribute("type") or ""

            # Skip early if field is already filled or checked
            if tag == "input":
                if input_type in ["checkbox", "radio"]:
                    if field.is_checked():
                        print(f"Skipping already selected checkbox/radio: {label_text}")
                        return
                else:
                    current_value = field.input_value().strip()
                    if current_value:
                        print(f"⏭️ Skipping already filled input: {label_text}")
                        return
            elif tag == "select":
                try:
                    current_value = field.input_value().strip().lower()
                    print(f"Current dropdown value for {label_text}: '{current_value}'")

                    # Skip if already answered with meaningful value
                    if current_value and current_value not in ["", "select", "select an option", "choose", "n/a"]:
                        print(f"Skipping already selected dropdown: {label_text}")
                        return

                    # Get answer and normalize
                    answer = get_answer_from_llm(label_text, file_id).strip()
                    answer = normalize_answer(answer)
                    print(f"Q: {label_text}")
                    print(f"A: {answer}")

                    if not answer:
                        print(f"No answer from LLM — skipping dropdown: {label_text}")
                        return

                    # Try to match option by text
                    options = field.query_selector_all("option")
                    matched = False
                    for opt in options:
                        opt_text = opt.inner_text().strip().lower()
                        if answer.lower() in opt_text or opt_text in answer.lower():
                            field.select_option(opt.get_attribute("value"))
                            print(f"Selected dropdown option: {opt_text}")
                            matched = True
                            break

                    if not matched:
                        print(f"Could not match dropdown option for: '{answer}' in: {label_text}")

                except Exception as e:
                    print(f"Failed to handle dropdown '{label_text}': {e}")


            elif tag == "textarea":
                current_value = field.input_value().strip()
                if current_value:
                    print(f" Skipping already filled textarea: {label_text}")
                    return
            answer = get_answer_from_llm(label_text, file_id)
            print(f"Q: {label_text}")
            print(f"A: {answer}")

            if tag == "input":

                if input_type in ["checkbox", "radio"]:
                    try:
                        field_id = field.get_attribute("id")
                        parent = None

                        if field_id:
                            escaped_id = css_escape(field_id)
                            field_locator = page.locator(f"#{escaped_id}")
                            parent = field_locator.locator("xpath=ancestor::*[self::fieldset or self::div][1]")
                        else:
                            # fallback to top container
                            parent = page.locator("div.jobs-easy-apply-modal")

                        options = parent.locator("input[type='radio'], input[type='checkbox']").all()
                        matched = False

                        for option in options:
                            try:
                                label = option.evaluate(
                                    """el => {
                                        const next = el.nextElementSibling;
                                        const parent = el.parentElement;
                                        return (next?.innerText || parent?.innerText || '').trim().toLowerCase();
                                    }"""
                                )
                                print(f"   → Found option: '{label}'")

                                if label and answer.lower() in label:
                                    try:
                                        option.check()
                                        print(f"Checked option using .check(): '{label}'")
                                    except Exception as e:
                                        print(f"check() failed: {e} — trying click()")

                                        try:
                                            option.click(force=True)
                                            print(f"Clicked option using force-click: '{label}'")
                                        except Exception as e2:
                                            print(f"Click also failed: {e2}")
                                            continue

                                    matched = True
                                    break

                            except Exception as e:
                                print(f"Error checking option: {e}")

                        if not matched:
                            print(f"No matching option found for answer: '{answer}'")
                    except Exception as e:
                        print(f"Error handling radio/checkbox group: {e}")

                else:
                    try:
                        # Special handling for city/location auto-suggest
                        if "location" in label_text.lower() or "city" in label_text.lower():
                            field.click()
                            field.fill(answer)
                            page.wait_for_timeout(1000)  # Wait for autosuggest dropdown
                            field.press("ArrowDown")
                            page.wait_for_timeout(500)
                            field.press("Enter")
                            print(" Selected location suggestion using keyboard.")
                        else:
                            field.fill(answer)
                            print(f" Filled input with: {answer}")
                    except Exception as e:
                        print(f" Failed to fill input: {e}")

            elif tag == "textarea":
                try:
                    field.fill(answer)
                    print(f" Filled textarea with: {answer}")
                except Exception as e:
                    print(f" Failed to fill textarea: {e}")

            else:
                print(f" Unsupported field tag: {tag}")
        except Exception as e:
            print(f" Error filling field for label '{label_text}': {e}")


    def process_fields_in_modal():
        try:
            modal = page.query_selector("div.jobs-easy-apply-modal")
            if not modal:
                print("Easy Apply modal not found.")
                return False

            labels = modal.query_selector_all("label, span, p")
            seen = set()

            for label in labels:
                label_text = label.inner_text().strip()

                if not label_text or label_text.lower() in seen:
                    continue

                # Skip answer-only labels like "Yes", "No"
                if label_text.lower() in {"yes", "no", "other", "none", "view", "back", "submit"}:
                    print(f"Skipping standalone option label: '{label_text}'")
                    continue

                field = None
                for_attr = label.get_attribute("for")
                if for_attr:
                    field = modal.query_selector(f"#{for_attr}")

                if not field:
                    field = label.query_selector("input, select, textarea")

                if not field:
                    # Try to find an input near the label
                    field = label.evaluate_handle("""
                        el => {
                            const container = el.closest('div, fieldset');
                            return container?.querySelector('input, select, textarea') || null;
                        }
                    """)

                if field:
                    seen.add(label_text.lower())
                    print(f"Label: {label_text}")
                    fill_field(field, label_text)

            return True

        except Exception as e:
            print(f"Error in modal field processing: {e}")
            return False

    while True:
        try:
            next_button = page.locator(
                "button:has-text('Next'), button:has-text('Review'), button:has-text('Submit')"
            ).first

            if not next_button or not next_button.is_enabled():
                print(" No enabled Next/Review/Submit button.")
                return

            btn_text = next_button.inner_text().strip()
            print(f"\n Clicking: {btn_text}")
            next_button.click()

            page.wait_for_timeout(2000)  # Give page time to update

            if btn_text.lower() == "submit":
                print(" Submitted. Looking for Done...")

                try:
                    #  Wait for Done/Close/Back to search button to appear
                    done_span = page.locator(
                        "span:has-text('Done'), span:has-text('Close'), span:has-text('Back to search')"
                    ).first
                    done_span.wait_for(state="visible", timeout=7000)
                    done_button = done_span.locator("xpath=ancestor::button[1]")

                    if done_button.is_visible() and done_button.is_enabled():
                        done_button.click()
                        print(" Clicked 'Done' button successfully.")
                    else:
                        print("️ Done not clickable. Forcing JS click.")
                        page.evaluate("btn => btn.click()", done_button)

                    #  Wait for modal to disappear (not required, but safe)
                    try:
                        page.wait_for_selector("div.jobs-easy-apply-modal", state="detached", timeout=5000)
                        print(" Modal closed.")
                    except:
                        print(" Modal may already be closed.")

                except Exception as e:
                    print(f" Done button failed: {e}")

                return
            modal = page.locator("div.jobs-easy-apply-modal").first
            try:
                modal.wait_for(state="visible", timeout=5000)
            except Exception:
                print(" Easy Apply modal not found or not visible.")
                return False

            process_fields_in_modal()

        except Exception as e:
            print(f" Navigation failed: {e}")
            return

def filter_easy_apply_jobs(page, file_id):
    applied_jobs = []
    try:
        filter_btn = page.locator("button:has-text('Easy Apply')").first
        filter_btn.click()
        print("Filtered to Easy Apply jobs")
        page.wait_for_timeout(3000)
    except Exception as e:
        print("Easy Apply filter error:", e)

    page.wait_for_selector("div.job-card-container", timeout=10000)
    jobs = page.query_selector_all("div.job-card-container")

    for idx, job in enumerate(jobs):
        if idx >= MAX_JOBS_PER_RUN:
            break
        try:
            job.click()
            page.wait_for_timeout(3000)
            apply_btn = page.query_selector("button.jobs-apply-button")
            if not apply_btn:
                print("Already applied — skipping this job.")
                continue

            job_title = page.query_selector("h2.topcard__title") or page.query_selector("h1")
            company_name = (
                    page.query_selector("a.topcard__org-name-link") or
                    page.query_selector("span.topcard__flavor") or
                    page.query_selector("div.artdeco-entity-lockup__subtitle")
            )
            location = (
                    page.query_selector("span.jobs-unified-top-card__bullet") or
                    page.query_selector("span.topcard__flavor--bullet") or
                    page.query_selector("div.artdeco-entity-lockup__caption")
            )

            job.click()
            page.wait_for_timeout(5000)

            right_panel = page.query_selector("div.jobs-details") or page.query_selector("div.jobs-search__job-details")
            if right_panel:
                right_panel.scroll_into_view_if_needed()
                page.mouse.wheel(0, 5000)
                page.wait_for_timeout(2000)

            job_description = page.query_selector("div.job-details-module.jobs-description")

            title_text = job_title.inner_text().strip() if job_title else "N/A"
            company_text = company_name.inner_text().strip() if company_name else "N/A"
            location_text = location.inner_text().strip() if location else "N/A"
            desc_text = job_description.inner_text().strip() if job_description else "N/A"

            apply_btn.click()
            page.wait_for_timeout(2000)

            try:
                extract_and_fill_form_fields_across_steps(page, file_id)
                fill_easy_apply_form_with_llm(page, file_id)
            except Exception as e:
                print(f"Skipping job due to LLM failure: {e}")
                close_button = page.query_selector("button:has-text('Discard'), button:has-text('Close')")
                if close_button:
                    close_button.click()
                    page.wait_for_selector("div.jobs-easy-apply-modal", state="detached", timeout=5000)
                continue  # Move to next job

            log_application_data(title_text, company_text, location_text, desc_text)
            page.wait_for_timeout(1000)

            done_button = page.query_selector(
                "button:has-text('Done'), button:has-text('Close'), button:has-text('Back to search')")
            next_btn = page.query_selector("button:has-text('Next')")
            review_btn = page.query_selector("button:has-text('Review')")
            submit_btn = page.query_selector("button:has-text('Submit')")

            # Only log job if one of these completes successfully
            applied = False

            if done_button and done_button.is_enabled():
                try:
                    done_button.click()
                    print(" Clicked Done/Close button.")
                    page.wait_for_selector("div.jobs-easy-apply-modal", state="detached", timeout=8000)
                    print(" Modal closed, ready to move to next job.")
                    applied = True
                except Exception as e:
                    print(f" Failed to click Done/Close: {e}")
                    page.screenshot(path="done_button_error.png")

            elif submit_btn and submit_btn.is_enabled():
                submit_btn.click()
                print(" Submitted application.")
                page.wait_for_timeout(4000)
                applied = True

            elif review_btn and review_btn.is_enabled():
                review_btn.click()
                print("Reviewing Application...")
                page.wait_for_timeout(2000)

            elif next_btn and next_btn.is_enabled():
                next_btn.click()
                print("Moving to next step...")
                page.wait_for_timeout(2000)

            else:
                print("No further steps.")

            # Only log after actual application
            if applied:
                applied_jobs.append({
                    "Job Title": title_text,
                    "Company Name": company_text,
                    "Location": location_text,
                    "Job Description": desc_text,
                })

            page.wait_for_timeout(3000)

        except Exception as e:
            print(f"Error in job #{idx + 1}: {e}")
            continue

    save_to_csv(applied_jobs)
    print(f"Total jobs applied: {len(applied_jobs)} out of max {MAX_JOBS_PER_RUN}")


def save_to_csv(data, filename="application_log.csv"):
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=[
            "Job Title", "Company Name", "Location", "Job Description", "form_labels"
        ])
        if not file_exists:
            writer.writeheader()
        for row in data:
            writer.writerow(row)


def fill_easy_apply_form_with_llm(page, file_id):
    try:
        modal = page.wait_for_selector("div.jobs-easy-apply-modal", timeout=7000)
    except Exception:
        print(" ..Easy Apply modal did not appear.")
        return

    labels = modal.query_selector_all("label, span, p")  # broaden span/p if labels are inside those
    for label in labels:
        label_text = label.inner_text().strip()
        if not label_text:
            continue
        print(f"Question: {label_text}")
        # Ask LLM for answer based on the label text question
        answer = get_answer_from_llm(label_text, file_id).strip()
        print(f"Answer from LLM: {answer}")

        # Find related input element:
        input_id = label.get_attribute("for")
        input_elem = None
        if input_id:
            input_elem = page.locator(f'input[id="{input_id}"]').first
        else:
            input_elem = label.query_selector("input, select, textarea")

        if not input_elem:
            print(f"  Could not find input element for question: {label_text}")
            continue

        tag_name = input_elem.evaluate("el => el.tagName.toLowerCase()")
        input_type = input_elem.get_attribute("type") or ""

        try:
            if tag_name == "input":
                if input_type in ["text", "number"]:
                    input_elem.fill(answer)

                elif input_type == "file":
                    try:
                        input_elem.set_input_files(RESUME_PATH)
                        print(f"Uploaded resume file: {RESUME_PATH}")
                    except Exception as e:
                        print(f"Failed to upload resume: {e}")
                elif input_type == "radio":
                    # Find radio buttons with same name and pick matching value
                    name = input_elem.get_attribute("name")
                    radios = page.query_selector_all(f"input[type=radio][name='{name}']")
                    for r in radios:
                        val = r.get_attribute("value")
                        if val and answer.lower() in val.lower():
                            r.check()
                            break
                elif input_type == "checkbox":
                    if answer.lower() in ["yes", "true", "1"]:
                        input_elem.check()
                    else:
                        input_elem.uncheck()
            elif tag_name == "select":
                # Select option matching the answer
                options = input_elem.query_selector_all("option")
                for opt in options:
                    opt_text = opt.inner_text().strip().lower()
                    if answer.lower() in opt_text:
                        input_elem.select_option(opt.get_attribute("value"))
                        break
            elif tag_name == "select":
                # Get all options and match answer
                options = input_elem.query_selector_all("option")
                matched = False
                for opt in options:
                    opt_text = opt.inner_text().strip().lower()
                    if answer.lower() in opt_text or opt_text in answer.lower():
                        input_elem.select_option(opt.get_attribute("value"))
                        matched = True
                        break
                if not matched:
                    print(f"No matching option for '{answer}' in select dropdown: {label_text}")

            elif tag_name == "textarea":
                input_elem.fill(answer)
            else:
                print(f"  Unsupported input type: {tag_name} / {input_type}")
        except Exception as e:
            print(f"  Error filling input for question '{label_text}': {e}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        login_to_linkedin(page)
        search_jobs(page)
        file_id = upload_resume_get_file_id(RESUME_PATH)  # <- Get file ID here
        filter_easy_apply_jobs(page, file_id)

        browser.close()


if __name__ == "__main__":
    main()
