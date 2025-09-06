import json
import time
import csv
import os
import requests
import random
import re
from playwright.sync_api import sync_playwright
from urllib.parse import quote
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path, override=True)
import psycopg2
from psycopg2.extras import execute_values

LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
RESUME_PATH = os.getenv("resume_path")
TARGET_JOB_TITLE = os.getenv("target_job_title")
TARGET_LOCATION = os.getenv("target_location")
LOG_FILE_PATH = os.getenv("log_file_path")
OPENWEBUI_API = os.getenv("OPENWEBUI_API_URL")
OPENWEBUI_MODEL = "gemma3:12b"
MAX_JOBS_PER_RUN = int(os.getenv("max_jobs_per_run", 50))
api_token = os.getenv("OPENWEBUI_API_KEY")

USER_NAME = "Manisha Walunj"
MODEL = "gemma3:12b"

with open("resume.txt", "r", encoding="utf-8") as file:
    resume_text = file.read()

def upload_resume_get_file_id(RESUME_PATH):
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

def search_linkedin_jobs_with_combined_input(page, job_title, job_location):
    try:
        encoded_title = quote(job_title)
        encoded_location = quote(job_location)
        search_url = (
            f"https://www.linkedin.com/jobs/search/?f_AL=true"
            f"&keywords={encoded_title}"
            f"&location={encoded_location}"
        )
        print(f"Navigating to: {search_url}")
        page.goto(search_url)
        page.wait_for_timeout(5000)
        print("Easy Apply job search loaded.")
    except Exception as e:
        print("Failed to load job search page:", e)

def discard_application(page):
    try:
        print("Attempting to discard application...")
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

def scroll_job_list(page, target_count=25):
    try:
        print("Scrolling job list...")
        page.wait_for_selector("div.job-card-container", timeout=10000)
        job_card = page.query_selector("div.job-card-container")
        if not job_card:
            raise Exception("No job cards found")
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
        max_same_count_tries = 4  # increased attempts
        for attempt in range(60):
            job_cards = page.query_selector_all("div.job-card-container")
            current_count = len(job_cards)
            # print(f"Found {current_count} jobs (attempt {attempt + 1})")
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
            page.evaluate("""
                (container) => {
                    container.scrollBy(0, 1000);
                }
            """, scroll_container)
            page.wait_for_timeout(1000)
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

def extract_and_fill_form_fields_across_steps(page, file_id):
    abort_flag = {"should_abort": False}
    global form_labels_collected
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
                        form_labels_collected[label_text] = selected_label  # ✅ Save

                        return
                else:
                    current_value = field.input_value().strip()
                    if current_value:
                        print(f"Already filled input: {label_text} = {current_value}")

                        return

            elif tag == "select":
                current_value = field.input_value().strip()
                if current_value and current_value.lower() not in ["", "select", "select an option", "choose", "n/a"]:
                    print(f"Already selected dropdown: {label_text} = {current_value}")
                    form_labels_collected[label_text] = selected_label  # ✅ Save

                    return

            elif tag == "textarea":
                current_value = field.input_value().strip()
                if current_value:
                    print(f"Already filled textarea: {label_text} = {current_value}")
                    return
            answer = get_answer_from_llm(label_text, file_id).strip()
            if not answer:
                print(f"No answer from LLM for: {label_text} — saving to unanswered file.")
                abort_flag["should_abort"] = True
                return

            print(f"Q: {label_text}")
            print(f"A: {answer}")
            form_labels_collected[label_text] = answer

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
                                    matched = True
                                    break
                                except Exception as e:
                                    print(f"check() failed: {e}")
                                    try:
                                        option.click(force=True)
                                        print(f"Clicked option: '{label}'")
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
                        else:
                            field.fill(answer)
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
                            # form_labels_collected.append(f"{label_text}: {opt_text}")
                            # add_label_answer(label_text, opt_text)
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
                    # add_label_answer(label_text, answer)
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
                skip_keywords = [
                    "submit", "next", "review", "done", "upload", "cover letter", "resume", "cv",
                    "dialog content", "powered by linkedin", "help center", "application settings",
                    "33%", "50%", "66%", "100%", "last used", "learn more", "view", "back", "doc", "pdf", "mb"
                ]
                if any(k in lower_label for k in skip_keywords):
                    continue

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

            continue_btn = page.locator("div.artdeco-modal button:has-text('Continue applying')").first
            if continue_btn and continue_btn.is_visible():
                print("Clicking 'Continue applying' button.")
                continue_btn.click()
                time.sleep(random.uniform(15, 40))

                page.wait_for_timeout(3000)
                # continue the loop (go back to form filling)
                continue

            # Then try to find navigation buttons
            next_button = page.locator(
                "button:has-text('Next'), button:has-text('Review'), button:has-text('Submit')").first

            if not next_button or not next_button.is_enabled():
                print("No enabled Next/Review/Submit button.")

                done_button = page.locator("button:has-text('Done')").first
                if done_button and done_button.is_visible():
                    print("Clicking Done button.")
                    done_button.click()
                    time.sleep(random.uniform(15, 40))
                    return True

                close_button = page.locator("button[aria-label='Dismiss'], button[aria-label='Close']").first
                if close_button and close_button.is_visible():
                    print("Clicking Close button to discard or exit modal.")
                    close_button.click()
                    time.sleep(random.uniform(15, 40))

                    return True

                print("No buttons found. Skipping job.")
                return False

            # Click navigation button
            btn_text = next_button.inner_text().strip()
            print(f"\nClicking: {btn_text}")
            page.wait_for_timeout(3000)
            next_button.click()
            time.sleep(random.uniform(15, 40))

            page.wait_for_timeout(8000)

            done_button = page.locator("button:has-text('Done')").first
            if done_button and done_button.is_visible():
                print("Detected Done button after clicking:", btn_text)
                done_button.click()
                time.sleep(random.uniform(15, 40))

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

def scrape_job_details(page, file_id, max_jobs=25):
    scraped_jobs = []
    processed_job_ids = set()
    CSV_FILE = "application_log.csv"
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=[
                "Job Title", "Company Name", "Location", "Job Description"
            ])
            writer.writeheader()
    page.wait_for_selector("div.job-card-container", timeout=10000)
    jobs = page.query_selector_all("div.job-card-container")
    if not jobs:
        print("No job cards found.")
        return scraped_jobs
    for idx, job in enumerate(jobs):
        if idx >= max_jobs:  # stop after max_jobs
            break
        try:
            job_id = job.get_attribute("data-job-id") or f"job-{idx}"
            if job_id in processed_job_ids:
                continue
            processed_job_ids.add(job_id)
            # Click each job to load details
            job.scroll_into_view_if_needed()
            job.click()
            page.wait_for_timeout(3000)

            apply_btn = page.query_selector("button.jobs-apply-button")
            if not apply_btn:
                print("Already applied — skipping.")
                continue
            # Extract job details
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
            # Clean text
            title_text = job_title.inner_text().strip() if job_title else "N/A"
            company_text = company_name.inner_text().strip() if company_name else "N/A"
            location_text = location.inner_text().strip() if location else "N/A"
            desc_text = job_description.inner_text().strip() if job_description else "N/A"

            apply_btn.click()
            page.wait_for_timeout(2000)
            extract_and_fill_form_fields_across_steps(page, file_id)
            # Save to list & CSV
            job_data = {
                "Job Title": title_text,
                "Company Name": company_text,
                "Location": location_text,
                "Job Description": desc_text
            }
            scraped_jobs.append(job_data)
            with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=job_data.keys())
                writer.writerow(job_data)
                writer.writerow({key: "-" * 20 for key in job_data.keys()})
            print(f"Saved job {idx+1}: {title_text} @ {company_text}")
        except Exception as e:
            print(f"Error scraping job #{idx + 1}: {e}")
            continue
    return scraped_jobs

DB_HOST = "localhost"
DB_NAME = "postgres"      # your database name
DB_USER = "postgres"      # your PostgreSQL username
DB_PASS = "2312"          # your PostgreSQL password

# def save_jobs_to_postgres(jobs):
#     if not jobs:
#         print("No jobs to save.")
#         return
#     try:
#         conn = psycopg2.connect(
#             host=DB_HOST,
#             database=DB_NAME,
#             user=DB_USER,
#             password=DB_PASS
#         )
#         cursor = conn.cursor()
#         insert_query = """
#             INSERT INTO linkedin_jobs (job_title, company_name, location, job_description)
#             VALUES %s
#         """
#         job_values = [
#             (job["Job Title"], job["Company Name"], job["Location"], job["Job Description"])
#             for job in jobs
#         ]
#         execute_values(cursor, insert_query, job_values)
#         conn.commit()
#         cursor.close()
#         conn.close()
#         print(f"{len(jobs)} jobs saved into PostgreSQL.")
#     except Exception as e:
#         print("Error saving to PostgreSQL:", e)

def save_job_with_answers(job):
    try:
        conn = psycopg2.connect(
            host="localhost",
            dbname="postgres",
            user="postgres",
            password="2312"
        )
        cursor = conn.cursor()

        # 🔍 Normalize Form Responses
        form_responses_json = []
        if "Form Responses" in job and job["Form Responses"]:
            responses = job["Form Responses"]

            # Case 1: dict {label: answer}
            if isinstance(responses, dict):
                form_responses_json = [
                    {"label": label, "answer": answer}
                    for label, answer in responses.items()
                ]

            # Case 2: list of {"label": ..., "answer": ...}
            elif isinstance(responses, list):
                form_responses_json = responses

        # 👉 Insert job into linkedin_jobs
        insert_job_query = """
            INSERT INTO linkedin_jobs (job_title, company_name, location, job_description, label, answer)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        cursor.execute(insert_job_query, (
            job.get("Job Title"),
            job.get("Company Name"),
            job.get("Location"),
            job.get("Job Description"),
            Json([r["label"] for r in form_responses_json]) if form_responses_json else Json([]),
            Json([r["answer"] for r in form_responses_json]) if form_responses_json else Json([])
        ))

        job_id = cursor.fetchone()[0]

        # 👉 Also insert into application_log (with job info + answers)
        if form_responses_json:
            log_values = [
                (
                    job_id,
                    job.get("Job Title"),
                    job.get("Company Name"),
                    job.get("Location"),
                    job.get("Job Description"),
                    r["label"],
                    r["answer"],
                    bool(r["answer"])
                )
                for r in form_responses_json
            ]
            insert_log_query = """
                INSERT INTO application_log
                (job_id, job_title, company_name, location, job_description, label, answer, is_answered)
                VALUES %s
            """
            execute_values(cursor, insert_log_query, log_values)

        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Job '{job['Job Title']}' and answers saved successfully.")

    except Exception as e:
        print("❌ Error saving to PostgreSQL:", e)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        login_to_linkedin(page)
        search_linkedin_jobs_with_combined_input(page, TARGET_JOB_TITLE, TARGET_LOCATION)
        file_id = upload_resume_get_file_id(RESUME_PATH)
        scroll_job_list(page, target_count=25)
        job = scrape_job_details(page, file_id, max_jobs=25)
        print("DEBUG JOB BEFORE SAVE:", job)
        save_job_with_answers(job)
    # browser.close()

if __name__ == "__main__":
    main()