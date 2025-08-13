
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
MAX_JOBS_PER_RUN = config.get("max_jobs_per_run", 50)
api_token = config["OPENWEBUI_API_KEY"]

USER_NAME = "Manisha Walunj"  # Change as needed
MODEL = "gemma3:12b"


def upload_resume_get_file_id(RESUME_PATH):
    cache_path = "resume_file_id.txt"

    # STEP 1: Check if cached file_id exists
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            file_id = f.read().strip()
            if file_id:
                print(f"Using cached file ID: {file_id}")
                return file_id

    # STEP 2: Upload resume and get new file_id
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json"
    }

    with open(RESUME_PATH, "rb") as f:
        files = {"file": f}
        resp = requests.post(f"{OPENWEBUI_API}/api/v1/files/", headers=headers, files=files, timeout=30)
        resp.raise_for_status()
        file_id = resp.json()["id"]
        print(f"Uploaded resume. File ID: {file_id}")

        # STEP 3: Save new file_id to cache
        with open(cache_path, "w") as f:
            f.write(file_id)

        return file_id

# def upload_resume_get_file_id(RESUME_PATH):
#     headers = {
#         "Authorization": f"Bearer {api_token}",
#         "Accept": "application/json"
#     }
#
#     with open(RESUME_PATH, "rb") as f:
#         files = {"file": f}
#         resp = requests.post(f"{OPENWEBUI_API}/api/v1/files/", headers=headers, files=files)
#         resp.raise_for_status()
#         file_id = resp.json()["id"]
#         print(f"Uploaded file. File ID: {file_id}")
#         return file_id  # Return it!
#

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
        json=payload,
    )
    response.raise_for_status()

    raw_answer = response.json()['choices'][0]['message']['content'].strip()
    # Clean unwanted characters
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
        # search_url = (
        #     f"https://www.linkedin.com/jobs/search/?keywords={encoded_title}"
        #     f"&location={encoded_location}&f_AL=true"
        # )
        search_url = (
            f"https://www.linkedin.com/jobs/search/?f_AL=true"
            f"&keywords={encoded_title}"
            f"&location={encoded_location}"
            # f"&f_E=2&f_WT=2"
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


def apply_to_multiple_pages(page, file_id, max_pages=10):
    current_page = 1
    applied_count = 0  # initialize only once here

    while current_page <= max_pages:
        print(f"\nStarting page {current_page}...")

        # scroll_job_list(page)
        applied_count = filter_easy_apply_jobs(page, file_id, applied_count)  # pass and get updated count

        try:
            page.wait_for_timeout(2000)

            next_btn = page.locator("button[aria-label*='View next page']")

            if next_btn.count() == 0:
                print("Next button not found.")
                break

            next_btn = next_btn.first
            next_btn.wait_for(state="attached", timeout=5000)
            next_btn.wait_for(state="visible", timeout=5000)

            page.evaluate("el => el.scrollIntoView({behavior: 'smooth', block: 'center'})", next_btn.element_handle())
            page.wait_for_timeout(1000)

            if next_btn.is_enabled():
                next_btn.click()
                print("Moved to next page...")
                page.wait_for_timeout(5000)
                current_page += 1
            else:
                print("Next button is disabled.")
                break

        except Exception as e:
            print(f"Pagination failed on page {current_page}: {e}")
            break

def scroll_job_list(page, target_count=30):
    try:
        print("Scrolling job list...")

        # Wait for a job card to appear to get a handle on the real scrollable container
        page.wait_for_selector("div.job-card-container", timeout=10000)
        job_card = page.query_selector("div.job-card-container")

        if not job_card:
            raise Exception("No job cards found")

        # Dynamically detect the scrollable parent container of the job card
        scroll_container = page.evaluate_handle("""
            (card) => {
                let el = card.parentElement;
                while (el && el.scrollHeight <= el.clientHeight) {
                    el = el.parentElement;
                }
                return el;
            }
        """, job_card)

        if not scroll_container:
            raise Exception("No scrollable container detected from job card")

        prev_count = -1
        same_count_tries = 0
        max_same_count_tries = 5  # increased attempts

        for attempt in range(60):
            job_cards = page.query_selector_all("div.job-card-container")
            current_count = len(job_cards)
            # print(f"📄 Found {current_count} jobs (attempt {attempt + 1})")

            if current_count >= target_count:
                print(f"Target of {target_count} jobs reached.")
                break

            if current_count == prev_count:
                same_count_tries += 1
                if same_count_tries >= max_same_count_tries:
                    print(f"Job count stuck at {current_count} after {same_count_tries} tries.")
                    break
            else:
                same_count_tries = 0

            prev_count = current_count

            # Scroll deeper manually to force loading
            page.evaluate("""
                (container) => {
                    container.scrollBy(0, 1000);
                }
            """, scroll_container)

            page.wait_for_timeout(1000)

            # Additional page down to help trigger new loads
            page.keyboard.press("PageDown")
            page.wait_for_timeout(1000)

        final_count = len(page.query_selector_all("div.job-card-container"))
        print(f"Final job count after scroll: {final_count}")

    except Exception as e:
        print(f"Error scrolling job list: {e}")
        print("Fallback full-page scroll...")
        for _ in range(40):
            page.keyboard.press("PageDown")
            page.wait_for_timeout(1000)
        print("Fallback scroll completed.")


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

def add_label_answer(label_text, answer):
    key = label_text.strip().lower()
    answer = str(answer).strip()

    # If label not seen yet, store it
    if key not in form_labels_collected:
        form_labels_collected[key] = f"{label_text}: {answer}"
    else:
        # Replace if new answer is longer/more complete
        existing_answer = form_labels_collected[key].split(":", 1)[1].strip()
        if len(answer) > len(existing_answer) and answer.lower() != "llm could not answer":
            form_labels_collected[key] = f"{label_text}: {answer}"


def extract_and_fill_form_fields_across_steps(page, file_id):
    abort_flag = {"should_abort": False}
    global form_labels_collected
    # form_labels_collected = []
    form_labels_collected = {}

    print("\nExtracting and filling form fields from all steps:")
    seen = set()

    def fill_field(field, label_text):
        try:

            if not field:
                print(f"No field found for label: {label_text}")
                return

            try:
                tag = field.evaluate("el => el?.tagName?.toLowerCase()")
            except Exception as e:
                print(f"Error evaluating tag for label '{label_text}': {e}")
                return

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
                        # form_labels_collected.append(f"{label_text}: {selected_label}")
                        add_label_answer(label_text, selected_label)

                        return
                else:
                    current_value = field.input_value().strip()
                    if current_value:
                        print(f"Already filled input: {label_text} = {current_value}")
                        # form_labels_collected.append(f"{label_text}: {current_value}")
                        add_label_answer(label_text, current_value)

                        return

            elif tag == "select":
                current_value = field.input_value().strip()
                if current_value and current_value.lower() not in ["", "select", "select an option", "choose", "n/a"]:
                    print(f"Already selected dropdown: {label_text} = {current_value}")
                    # form_labels_collected.append(f"{label_text}: {current_value}")
                    add_label_answer(label_text, current_value)

                    return

            elif tag == "textarea":
                current_value = field.input_value().strip()
                if current_value:
                    print(f"Already filled textarea: {label_text} = {current_value}")
                    # form_labels_collected.append(f"{label_text}: {current_value}")
                    add_label_answer(label_text, current_value)

                    return

            # Otherwise, get answer from LLM
            answer = get_answer_from_llm(label_text, file_id).strip()
            if not answer:
                print(f"No answer from LLM for: {label_text} — skipping job.")
                # form_labels_collected.append(f"{label_text}: LLM could not answer")
                add_label_answer(label_text, "LLM could not answer")

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
                            # form_labels_collected.append(f"{label_text}: {answer}")
                            add_label_answer(label_text, answer)

                        else:
                            field.fill(answer)
                            # form_labels_collected.append(f"{label_text}: {answer}")
                            add_label_answer(label_text, answer)

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
                    # form_labels_collected.append(f"{label_text}: {answer}")
                    add_label_answer(label_text, answer)

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
                if not label_text or len(label_text) > 200:
                    continue

                lower_label = label_text.lower()
                if lower_label in seen:
                    continue
                seen.add(lower_label)

                # Skip system/resume-related labels
                skip_keywords = [
                    "submit", "next", "review", "done", "upload", "cover letter", "resume", "cv",
                    "dialog content", "powered by linkedin", "help center", "application settings",
                    "33%", "50%", "66%", "100%", "last used", "learn more", "view", "back", "doc", "pdf", "mb"
                ]
                if any(k in lower_label for k in skip_keywords):
                    # print(f"Skipping system/upload label: {label_text}")
                    continue

                # Skip yes/no or answer-only labels
                if lower_label in {"yes", "no", "none", "other", "submit"}:
                    print(f"Skipping standalone option label: '{label_text}'")
                    continue

                field = None
                for_attr = label.get_attribute("for")
                if for_attr:
                    field = modal.query_selector(f"#{for_attr}")
                if not field:
                    field = label.query_selector("input, select, textarea")
                if not field:
                    js_handle = label.evaluate_handle("el => el.closest('div, fieldset')?.querySelector('input, select, textarea') || null")
                    field = js_handle.as_element() if js_handle else None

                if not field:
                    continue

                input_type = field.get_attribute("type") or ""
                if input_type == "file" or any(kw in lower_label for kw in ["resume", "cover letter", "cv"]):
                    value = field.evaluate("el => el?.value || ''").strip()
                    if value:
                        print(f"Resume/Cover Letter already uploaded: {label_text} — skipping.")
                        continue
                    print(f"File upload input found (no value) — skipping without discarding: {label_text}")
                    continue

                print(f"Label: {label_text}")
                fill_field(field, label_text)

            if abort_flag["should_abort"]:
                print("LLM failed to answer a required field — discarding application.")
                discard_application(page)
                return False

            return True
        except Exception as e:
            print(f"Error in modal field processing: {e}")
            return False

    while True:
        try:
            # First process & print all labels for this step
            if not process_fields_in_modal():
                print("Modal aborted.")
                return False

            # Then try to find navigation buttons
            next_button = page.locator(
                "button:has-text('Next'), button:has-text('Review'), button:has-text('Submit')").first

            if not next_button or not next_button.is_enabled():
                print("No enabled Next/Review/Submit button.")

                done_button = page.locator("button:has-text('Done')").first
                if done_button and done_button.is_visible():
                    print("Clicking Done button.")
                    done_button.click()
                    return True

                close_button = page.locator("button[aria-label='Dismiss'], button[aria-label='Close']").first
                if close_button and close_button.is_visible():
                    print("Clicking Close button to discard or exit modal.")
                    close_button.click()
                    return True

                print("No buttons found. Skipping job.")
                return False

            # Click navigation button
            btn_text = next_button.inner_text().strip()
            print(f"\nClicking: {btn_text}")
            page.wait_for_timeout(3000)
            next_button.click()
            page.wait_for_timeout(8000)

            done_button = page.locator("button:has-text('Done')").first
            if done_button and done_button.is_visible():
                print("Detected Done button after clicking:", btn_text)
                done_button.click()
                return True

            if not process_fields_in_modal():
                print("Modal aborted.")
                return False

        except Exception as e:
            print(f"Error during form navigation: {e}")
            try:
                close_button = page.locator("button[aria-label='Dismiss'], button[aria-label='Close']").first
                if close_button and close_button.is_visible():
                    print("Clicking Close button after exception.")
                    close_button.click()
            except:
                pass
            return False

def filter_easy_apply_jobs(page, file_id, applied_count, already_scrolled=False):
    applied_jobs = []
    processed_job_ids = set()

    if not already_scrolled:
        scroll_job_list(page)

    while applied_count < MAX_JOBS_PER_RUN:
        page.wait_for_selector("div.job-card-container", timeout=10000)
        jobs = page.query_selector_all("div.job-card-container")

        if not jobs:
            print("No job cards found.")
            break

        for idx, job in enumerate(jobs):
            job_id = job.get_attribute("data-job-id") or job.inner_text().strip()
            if job_id in processed_job_ids:
                continue

            processed_job_ids.add(job_id)

            try:
                job.scroll_into_view_if_needed()
                job.click()
                page.wait_for_timeout(3000)

                apply_btn = page.query_selector("button.jobs-apply-button")
                if not apply_btn:
                    print("Already applied — skipping.")
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
                right_panel = page.query_selector("div.jobs-details") or page.query_selector("div.jobs-search__job-details")
                if right_panel:
                    right_panel.scroll_into_view_if_needed()
                    page.mouse.wheel(0, 5000)
                    page.wait_for_timeout(1500)

                job_description = page.query_selector("div.job-details-module.jobs-description")

                title_text = job_title.inner_text().strip() if job_title else "N/A"
                company_text = company_name.inner_text().strip() if company_name else "N/A"
                location_text = location.inner_text().strip() if location else "N/A"
                desc_text = job_description.inner_text().strip() if job_description else "N/A"

                apply_btn.click()
                page.wait_for_timeout(2000)

                try:
                    global form_labels_collected
                    form_labels_collected = []
                    form_labels = extract_and_fill_form_fields_across_steps(page, file_id)

                    CSV_FILE = "application_log.csv"

                    # Write headers once if file doesn't exist
                    if not os.path.exists(CSV_FILE):
                        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as file:
                            writer = csv.DictWriter(file, fieldnames=[
                                "Job Title", "Company Name", "Location", "Job Description", "form_labels"
                            ])
                            writer.writeheader()

                    # Always save, even if application was discarded
                    # form_labels_text = "\n".join(form_labels_collected) if form_labels_collected else "LLM could not answer or modal skipped."
                    form_labels_text = "\n".join(form_labels_collected.values()) if form_labels_collected else "LLM could not answer or modal skipped."


                    job_data = {
                        "Job Title": title_text,
                        "Company Name": company_text,
                        "Location": location_text,
                        "Job Description": desc_text,
                        "form_labels": form_labels_text
                    }

                    applied_jobs.append(job_data)

                    # Save immediately to CSV
                    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as file:
                        writer = csv.DictWriter(file, fieldnames=job_data.keys())
                        writer.writerow(job_data)

                    if form_labels:
                        applied_count += 1
                        print(f"Applied to job {applied_count}/{MAX_JOBS_PER_RUN}")
                        page.wait_for_timeout(3000)
                    else:
                        print("Job discarded after saving unanswered questions.")

                except Exception as e:
                    print(f"LLM failure: {e} — discarding modal...")
                    close_button = page.query_selector("button:has-text('Discard'), button:has-text('Close')")
                    if close_button:
                        close_button.click()
                        page.wait_for_selector("div.jobs-easy-apply-modal", state="detached", timeout=5000)
                    continue

            except Exception as e:
                print(f"Error in job #{idx + 1}: {e}")
                continue

        break  # One full scroll pass per page

    print(f"Jobs collected to write in CSV: {len(applied_jobs)}")
    for job in applied_jobs:
        print(job)

    save_to_csv(applied_jobs)
    print(f"Total jobs applied: {applied_count} out of max {MAX_JOBS_PER_RUN}")
    return applied_count


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

                # elif input_type == "file":
                #     try:
                #         input_elem.set_input_files(RESUME_PATH)
                #         print(f"Uploaded resume file: {RESUME_PATH}")
                #     except Exception as e:
                #         print(f"Failed to upload resume: {e}")
                elif input_type == "file":
                    print(f"Skipping file upload for: {label_text}")

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
        apply_to_multiple_pages(page, file_id, max_pages=5)
        browser.close()


if __name__ == "__main__":
    main()









