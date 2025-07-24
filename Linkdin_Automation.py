import re
import time
import json
import csv
import os
import requests
from playwright.sync_api import sync_playwright
from urllib.parse import quote

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
                    f"(e.g., Angular, Node.js), extract that number from the resume if clearly present. "
                    f"If not mentioned or unclear, leave the answer completely blank.\n\n"

                    f"If the question is about eligibility (Yes/No), answer only 'Yes' or 'No'. "
                    f"If you're unsure, leave the answer blank.\n\n"

                    f"If it's a multiple-choice question (radio or checkbox), pick the most relevant option exactly as shown. "
                    f"If not enough information is available, leave it blank.\n\n"

                    f"Do not include explanations. If there's no clear answer from the resume, return nothing.\n\n"

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

    raw_answer = response.json()['choices'][0]['message']['content'].strip()

    # Clean unwanted characters
    import re
    cleaned = re.sub(r"^\s*(\d+\.)\s*", "", raw_answer)  # remove "1. "
    cleaned = re.sub(r"^\s*[-•]\s*", "", cleaned)        # remove bullets

    # Treat obviously invalid answers as blank
    if not cleaned or cleaned.strip().lower() in ["0", "no", "none", "not sure", "n/a", "na", "i don't know", "unknown"]:
        return ""

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

def search_linkedin_jobs_with_combined_input(page, job_title, job_location):

    try:
        encoded_title = quote(job_title)
        encoded_location = quote(job_location)

        # Add Easy Apply filter directly in URL
        search_url = (
            f"https://www.linkedin.com/jobs/search/?keywords={encoded_title}"
            f"&location={encoded_location}&f_AL=true"
        )

        print(f"Navigating to: {search_url}")
        page.goto(search_url)
        page.wait_for_timeout(5000)
        print("Easy Apply job search loaded.")
    except Exception as e:
        print("Failed to load job search page:", e)


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

def discard_application(page):
    try:
        print("Attempting to discard application...")

        # Step 1: Click the 'Dismiss' or 'Close' button to trigger save modal
        close_button = page.query_selector("button[aria-label='Dismiss'], button[aria-label='Close']")
        if close_button:
            close_button.click()
            print("Clicked close on Easy Apply modal.")
        else:
            print("Close button not found.")
            return

        # Step 2: Wait for the 'Save this application?' modal
        discard_button = page.locator("button:has-text('Discard')")
        if discard_button.is_visible(timeout=3000):
            discard_button.click()
            print("Discarded application via Cancel → Discard.")
        else:
            print("Discard button not visible after cancel.")
            return

        # Step 3: Confirm modal is closed
        page.wait_for_selector("div.jobs-easy-apply-modal", state="detached", timeout=5000)

    except Exception as e:
        print(f"Error while discarding application: {e}")



def handle_done_confirmation(page):
    try:
        print("Waiting for confirmation modal...")

        page.wait_for_selector("div.artdeco-modal", timeout=8000)
        print("Confirmation modal appeared.")

        done_button = page.locator("div.artdeco-modal button:has-text('Done')").first
        done_button.wait_for(state="visible", timeout=8000)

        if done_button and done_button.is_enabled():
            done_button.click()
            print("Clicked 'Done' button.")
        else:
            print("Done button not clickable — trying JS fallback...")

            handle = done_button.element_handle()
            if handle:
                page.evaluate("btn => btn.click()", handle)
                print("Fallback JS click succeeded.")
            else:
                print("Could not retrieve element handle for Done button.")

        # Wait for modal to disappear
        page.wait_for_selector("div.artdeco-modal", state="detached", timeout=5000)
        print("Confirmation modal closed.")

    except Exception as e:
        print(f"Failed to handle confirmation modal: {e}")
        page.screenshot(path="done_failed.png")

def extract_and_fill_form_fields_across_steps(page, file_id):
    abort_flag = {"should_abort": False}
    global form_labels_collected
    form_labels_collected = []

    print("\nExtracting and filling form fields from all steps:")
    seen = set()
    def fill_field(field, label_text):
        try:

            if not field:
                print(f"No field found for label: {label_text}")
                return

            tag = field.evaluate("el => el.tagName.toLowerCase()")
            input_type = field.get_attribute("type") or ""

            # Handle already filled input
            if tag == "input":
                if input_type in ["checkbox", "radio"]:
                    if field.is_checked():
                        selected_label = field.evaluate(
                            """el => {
                                const next = el.nextElementSibling;
                                const parent = el.parentElement;
                                return (next?.innerText || parent?.innerText || 'Yes').trim();
                            }"""
                        )
                        print(f"Already selected: {label_text} = {selected_label}")
                        form_labels_collected.append(f"{label_text}: {selected_label}")
                        return
                else:
                    current_value = field.input_value().strip()
                    if current_value:
                        print(f"Already filled input: {label_text} = {current_value}")
                        form_labels_collected.append(f"{label_text}: {current_value}")
                        return

            elif tag == "select":
                current_value = field.input_value().strip()
                if current_value and current_value.lower() not in ["", "select", "select an option", "choose", "n/a"]:
                    print(f"Already selected dropdown: {label_text} = {current_value}")
                    form_labels_collected.append(f"{label_text}: {current_value}")
                    return

            elif tag == "textarea":
                current_value = field.input_value().strip()
                if current_value:
                    print(f"Already filled textarea: {label_text} = {current_value}")
                    form_labels_collected.append(f"{label_text}: {current_value}")
                    return

            # Otherwise, get answer from LLM
            answer = get_answer_from_llm(label_text, file_id).strip()
            if not answer:
                print(f"No answer from LLM for: {label_text} — skipping job.")
                form_labels_collected.append(f"{label_text}: LLM could not answer")
                abort_flag["should_abort"] = True
                return

            print(f"Q: {label_text}")
            print(f"A: {answer}")

            if tag == "input":
                if input_type in ["checkbox", "radio"]:
                    try:
                        field_id = field.get_attribute("id")
                        if field_id:
                            escaped_id = css_escape(field_id)
                            parent = page.locator(f"#{escaped_id}").locator(
                                "xpath=ancestor::*[self::fieldset or self::div][1]")
                        else:
                            parent = page.locator("div.jobs-easy-apply-modal")

                        options = parent.locator("input[type='radio'], input[type='checkbox']").all()
                        matched = False
                        for option in options:
                            label = option.evaluate(
                                """el => {
                                    const next = el.nextElementSibling;
                                    const parent = el.parentElement;
                                    return (next?.innerText || parent?.innerText || '').trim().toLowerCase();
                                }"""
                            )
                            print(f" → Found option: '{label}'")

                            if label and (
                                    label == answer.strip().lower()
                                    or answer.strip().lower() in label
                                    or is_similar(label, answer)
                            ):
                                try:
                                    option.check()
                                    print(f"Checked option: '{label}'")
                                    form_labels_collected.append(f"{label_text}: {label}")
                                    matched = True
                                    break
                                except Exception as e:
                                    print(f"check() failed: {e}")
                                    try:
                                        option.click(force=True)
                                        print(f"Clicked option: '{label}'")
                                        form_labels_collected.append(f"{label_text}: {label}")
                                        matched = True
                                        break
                                    except Exception as e2:
                                        print(f"Click also failed: {e2}")
                        if not matched:
                            print(f"No matching option found for: '{answer}'")
                    except Exception as e:
                        print(f"Error handling checkbox/radio group: {e}")
                else:
                    try:
                        if "location" in label_text.lower() or "city" in label_text.lower():
                            field.click()
                            field.fill(answer)
                            page.wait_for_timeout(1000)
                            field.press("ArrowDown")
                            page.wait_for_timeout(500)
                            field.press("Enter")
                            print("Selected location using keyboard.")
                            form_labels_collected.append(f"{label_text}: {answer}")
                        else:
                            field.fill(answer)
                            form_labels_collected.append(f"{label_text}: {answer}")
                            print(f"Filled input with: {answer}")
                    except Exception as e:
                        print(f"Failed to fill input: {e}")

            elif tag == "select":
                try:
                    options = field.query_selector_all("option")
                    matched = False
                    for opt in options:
                        opt_text = opt.inner_text().strip().lower()
                        if answer.lower() in opt_text or opt_text in answer.lower():
                            field.select_option(opt.get_attribute("value"))
                            print(f"Selected dropdown option: {opt_text}")
                            form_labels_collected.append(f"{label_text}: {opt_text}")
                            matched = True
                            break
                    if not matched:
                        print(f"Could not match dropdown option for: '{answer}'")
                except Exception as e:
                    print(f"Failed to handle dropdown '{label_text}': {e}")

            elif tag == "textarea":
                try:
                    field.fill(answer)
                    form_labels_collected.append(f"{label_text}: {answer}")
                    print(f"Filled textarea with: {answer}")
                except Exception as e:
                    print(f"Failed to fill textarea: {e}")
            else:
                print(f"Unsupported field tag: {tag}")
        except Exception as e:
            print(f"Error filling field '{label_text}': {e}")

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

                # Skip empty or system labels
                if not label_text or len(label_text) > 200:
                    continue

                lower_label = label_text.lower()
                system_keywords = [
                    "submit", "next", "review", "done", "dialog content", "powered by linkedin", "help center",
                    "application settings", "notice of employment rights", "100%", "last used", "learn more",
                    "stay up to date", "view", "back", "resume", "upload resume", "select resume", "cv",
                    "33%", "upload", "doc", "pdf", "notice"
                ]
                if any(k in lower_label for k in system_keywords):
                    print(f"Skipping system label: {label_text}")
                    continue

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
                    if any(p in label_text for p in ["%", "MB", "KB"]):
                        print(f"Skipping non-field label: {label_text}")
                        continue

                    seen.add(label_text.lower())
                    print(f"Label: {label_text}")
                    fill_field(field, label_text)

            filled_fields = len(seen)

            if filled_fields == 0:
                print("No fillable fields found. Continuing...")
                return True

            if abort_flag["should_abort"]:
                print("LLM failed to answer a required field — closing modal.")
                discard_application(page)
                return False

            return form_labels_collected

        except Exception as e:
            print(f"Error in modal field processing: {e}")
            return False

    # Step 1: Fill all modal steps
    while True:
        try:
            next_button = page.locator(
                "button:has-text('Next'), button:has-text('Review'), button:has-text('Submit')"
            ).first

            if not next_button or not next_button.is_enabled():
                print("No enabled Next/Review/Submit button.")
                return False

            btn_text = next_button.inner_text().strip()
            print(f"\nClicking: {btn_text}")

            next_button.click()
            page.wait_for_timeout(5000)

            # Check if Done button appeared => submission happened
            done_button = page.locator("button:has-text('Done')").first
            if done_button and done_button.is_visible():
                print("Detected Done button after clicking:", btn_text)
                done_button.click()
                return True  # move to next job

            # If not submitted, continue filling
            modal = page.locator("div.jobs-easy-apply-modal").first
            modal.wait_for(state="visible", timeout=5000)

            success = process_fields_in_modal()
            if not success:
                print("Modal aborted due to missing LLM answer.")
                return False

        except Exception as e:
            print(f"Error during form navigation: {e}")
            return False

def filter_easy_apply_jobs(page, file_id):
    applied_jobs = []
    applied_count = 0  # Count how many jobs were actually applied
    page.wait_for_selector("div.job-card-container", timeout=10000)
    jobs = page.query_selector_all("div.job-card-container")
    for idx, job in enumerate(jobs):
        if applied_count >= MAX_JOBS_PER_RUN:
            break  # Stop only when enough jobs have been applied

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
                global form_labels_collected
                form_labels_collected = []  # reset for each job

                form_labels = extract_and_fill_form_fields_across_steps(page, file_id)

                if form_labels:
                    form_labels_text = "\n".join(form_labels_collected) if form_labels_collected else "LLM could not answer or modal skipped."

                    applied_jobs.append({
                        "Job Title": title_text,
                        "Company Name": company_text,
                        "Location": location_text,
                        "Job Description": desc_text,
                        "form_labels": form_labels_text
                    })
                    continue

            except Exception as e:
                print(f"Skipping job due to LLM failure: {e}")
                close_button = page.query_selector("button:has-text('Discard'), button:has-text('Close')")
                if close_button:
                    close_button.click()
                    page.wait_for_selector("div.jobs-easy-apply-modal", state="detached", timeout=5000)
                continue

            # Only log and count after actual application
            applied_jobs.append({
                "Job Title": title_text,
                "Company Name": company_text,
                "Location": location_text,
                "Job Description": desc_text,
                "form_labels": "\n".join(form_labels) if form_labels else "\n".join(form_labels_collected)
            })

            applied_count += 1  # Increment after successful application
            print(f"Applied to job {applied_count}/{MAX_JOBS_PER_RUN}")

            page.wait_for_timeout(3000)

        except Exception as e:
            print(f"Error in job #{idx + 1}: {e}")
            continue

    print(f"Jobs collected to write in CSV: {len(applied_jobs)}")
    for job in applied_jobs:
        print(job)

    save_to_csv(applied_jobs)
    print(f"Total jobs applied: {applied_count} out of max {MAX_JOBS_PER_RUN}")


def save_to_csv(applied_jobs):
    log_file = 'application_log.csv'
    file_exists = os.path.isfile(log_file)
    with open(log_file, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:

            writer.writerow([
                'Job Title',
                'Company Name',
                'Location',
                'Job Description',
                'Form Labels and Answers'
            ])

        for job in applied_jobs:
            writer.writerow([
                job.get("Job Title", ""),
                job.get("Company Name", ""),
                job.get("Location", ""),
                job.get("Job Description", ""),
                job.get("form_labels", "")
            ])


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
        search_linkedin_jobs_with_combined_input(page, TARGET_JOB_TITLE, TARGET_LOCATION)
        file_id = upload_resume_get_file_id(RESUME_PATH)  # <- Get file ID here
        filter_easy_apply_jobs(page, file_id)

        browser.close()


if __name__ == "__main__":
    main()







