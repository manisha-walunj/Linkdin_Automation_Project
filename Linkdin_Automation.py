#--------Linkdin Automation-------------------------------#

from datetime import datetime
import time
import json
import csv
import os
import requests
from playwright.sync_api import sync_playwright
import re


def normalize(text):
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', text.lower().strip()))

with open("config.json", "r") as f:
    config = json.load(f)

with open("resume.txt", "r", encoding="utf-8") as file:
    resume_text = file.read()

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
# MODEL = "gemma3"

MANUAL_ANSWER_FILE = "manual_answers.json"

def extract_skill_from_question(question: str) -> str:
    match = re.search(r"experience.*?\b(?:in|with)\b\s+([\w.+#-]+)", question, re.I)
    if match:
        return match.group(1).strip()
    return ""


def load_manual_answers():
    if os.path.exists(MANUAL_ANSWER_FILE):
        with open(MANUAL_ANSWER_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
            return {normalize(k): v for k, v in raw.items()}
    return {}

def save_manual_answers(answers_dict):
    normalized_dict = {normalize(k): v for k, v in answers_dict.items()}
    with open(MANUAL_ANSWER_FILE, "w", encoding="utf-8") as f:
        json.dump(normalized_dict, f, ensure_ascii=False, indent=2)

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

def log_application_data(job_title, company_name, location, description, qna_pairs=None):
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
                'Questions',
                'Answers'
            ])

        questions = "; ".join([q for q, a in qna_pairs]) if qna_pairs else ""
        answers = "; ".join([a for q, a in qna_pairs]) if qna_pairs else ""

        writer.writerow([
            job_title,
            company_name,
            location,
            description,
            questions,
            answers
        ])

def get_answer_from_llm(question, file_id, manual_answers):
    normalized_question = normalize(question)

    # 1. First check manual answers
    if normalized_question in manual_answers:
        saved = manual_answers[normalized_question].strip()
        if saved:
            print(f"Reused manual answer for: '{question}'")
            return saved

    # 2. Check if the skill exists in resume before asking LLM
    skill = extract_skill_from_question(question)
    if skill and skill.lower() not in resume_text.lower():
        print(f"'{skill}' not found in resume. Skipping question: {question}")
        return "0"

    # 3. Ask LLM
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
                    f"based only on the resume content below.\n\n"
                    f"If the question is about eligibility (Yes/No), always answer either 'Yes' or 'No'.\n"
                    f"Only return '0' for numeric experience questions.\n"
                    f"If the question is about years of experience with a specific skill or technology "
                    f"(e.g., Angular, Node.js), extract that number from the resume if present. "
                    f"Return a whole number between 0 and 30. If it's not mentioned, return 0.\n"
                    f"If unsure, answer 0 for years or No for eligibility.\n\n"
                    f"Resume:\n{resume_text}\n\n"
                    f"Question: {question}"
                )
            }
        ],
        "temperature": 0.3
    }

    try:
        response = requests.post(
            f"{OPENWEBUI_API}/api/chat/completions",
            headers=chat_headers,
            json=payload
        )
        response.raise_for_status()
        answer = response.json()['choices'][0]['message']['content'].strip()

        # 4. If LLM returns 0 or No, ask you manually and save
        if answer.lower() in ["", "0", "no", "n/a"]:
            manual = input(f"LLM uncertain for: '{question}' — Please enter manually: ").strip()
            if manual:
                manual_answers[normalized_question] = manual
                save_manual_answers(manual_answers)
                print(f"Using manual answer: '{manual}'")
                time.sleep(1)
                return manual
        else:
            return answer

    except Exception as e:
        print(f"Error from LLM API: {e}")
        if 'response' in locals():
            print(f"LLM API response text: {response.text}")
        manual = input(f"Failed to get LLM answer. Enter manually for '{question}': ").strip()
        if manual:
            manual_answers[normalized_question] = manual
            save_manual_answers(manual_answers)
            return manual
        return ""


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

def extract_and_fill_form_fields_across_steps(page, file_id, manual_answers):
    print("\n📋 Extracting and filling form fields from all steps:")
    seen = set()
    qna_pairs = []


    def fill_field(field, label_text):
        try:
            tag = field.evaluate("el => el.tagName.toLowerCase()")
            input_type = field.get_attribute("type") or ""
            answer = None
            is_prefilled = False

            # Check if field already has value
            if tag == "input":
                if input_type == "checkbox":
                    if field.is_checked():
                        print(f"Skipping already selected checkbox: {label_text}")
                        answer = "Already selected"
                        is_prefilled = True
                else:
                    current_value = field.input_value().strip()
                    if current_value:
                        print(f"Skipping already filled input: {label_text}")
                        answer = current_value
                        is_prefilled = True



            elif input_type == "radio":

                try:

                    parent = field.locator("xpath=ancestor::fieldset[1] | ancestor::div[1]")
                    radios = parent.query_selector_all("input[type='radio']")
                    matched = False
                    for radio in radios:
                        radio_label = radio.evaluate(
                            """el => {
                                let label = el.nextElementSibling?.innerText || el.labels?.[0]?.innerText || '';
                                return label.trim().toLowerCase();
                            }"""
                        )
                        if answer.lower() in radio_label:
                            radio.check()
                            print(f"Selected radio: '{radio_label}'")
                            matched = True
                            break
                    if not matched:
                        print(f"No matching radio found for: '{answer}' in group: {label_text}")
                    return
                except Exception as e:
                    print(f"Radio selection failed: {e}")
                return
            elif tag == "textarea":
                current_value = field.input_value().strip()
                if current_value:
                    print(f"Skipping already filled textarea: {label_text}")
                    answer = current_value
                    is_prefilled = True
            elif tag == "select":
                try:
                    selected_option = field.query_selector("option:checked")
                    selected_text = selected_option.inner_text().strip().lower() if selected_option else ""
                    if selected_text in ["", "select", "select an option", "choose", "choose an option", "none", "n/a",
                                         "month", "year"]:
                        print(f"Dropdown needs filling for: {label_text} (value: '{selected_text}')")
                    else:
                        print(f"Skipping already selected dropdown: {label_text} (value: '{selected_text}')")
                        return
                except Exception as e:
                    print(f"Error checking dropdown value: {e}")
            # Get answer from LLM or manual input
            if not is_prefilled:
                # Handle From*/To* special case for LinkedIn dates
                if label_text.strip().lower() in ["from*", "to*", "from", "to"]:
                    try:
                        parent = field.locator("xpath=ancestor::div[1]")
                        dropdowns = parent.query_selector_all("select")
                        if len(dropdowns) == 2:
                            month = "January"
                            year = "2023"

                            for opt in dropdowns[0].query_selector_all("option"):
                                if month.lower() in opt.inner_text().strip().lower():
                                    dropdowns[0].select_option(opt.get_attribute("value"))
                                    break

                            for opt in dropdowns[1].query_selector_all("option"):
                                if year in opt.inner_text().strip():
                                    dropdowns[1].select_option(opt.get_attribute("value"))
                                    break

                            print(f"Filled {label_text} with {month} {year}")
                            return
                        else:
                            print(f"Expected 2 dropdowns for date field, found {len(dropdowns)}")
                    except Exception as e:
                        print(f"Failed to fill '{label_text}' date dropdowns: {e}")
                    return

                answer = get_answer_from_llm(label_text, file_id, manual_answers).strip()
                if not answer or answer.lower() in ["", "n/a"]:
                    print(f"Skipping field due to invalid or empty answer: '{label_text}'")
                    return
                print(f"Using LLM/manual → Q: {label_text} | A: {answer}")
            else:
                print(f"Used existing value → Q: {label_text} | A: {answer}")

            qna_pairs.append((label_text, answer))
            if not is_prefilled:
                if tag == "input":
                    if input_type == "checkbox":
                        parent = field.locator("xpath=ancestor::fieldset[1] | ancestor::div[1]")
                        matched = False
                        options = parent.locator("label, div").all()
                        for option in options:
                            try:
                                label = option.inner_text().strip().lower()
                                if label and answer.lower() in label:
                                    option.click()
                                    print(f"Clicked checkbox: '{label}'")
                                    matched = True
                                    break
                            except Exception as e:
                                print(f"Error clicking checkbox option: {e}")
                        if not matched:
                            try:
                                if answer.lower() in ["yes", "true", "1"]:
                                    field.check()
                                    print(f"Checked box for: {label_text}")
                                else:
                                    field.uncheck()
                                    print(f"Unchecked box for: {label_text}")
                            except Exception as e:
                                print(f"Error checking/unchecking box: {e}")
                    else:
                        if "location" in label_text.lower() or "city" in label_text.lower():
                            try:
                                field.click()
                                field.fill(answer)
                                page.wait_for_timeout(1000)
                                field.press("ArrowDown")
                                page.wait_for_timeout(500)
                                field.press("Enter")
                                print("Selected first autosuggest option via keyboard.")
                            except Exception as e:
                                print(f"Failed to select location suggestion: {e}")
                            return
                        else:
                            field.fill(answer)
                            print(f"Filled input with: {answer}")

                elif tag == "select":
                    options = field.query_selector_all("option")
                    normalized_answer = answer.lower().strip()
                    option_texts = [opt.inner_text().strip().lower() for opt in options]

                    if normalized_answer == "0" and "yes" in option_texts and "no" in option_texts:
                        print("Interpreting '0' as 'No' for Yes/No dropdown")
                        normalized_answer = "no"

                    matched = False
                    for opt in options:
                        opt_text = opt.inner_text().strip().lower()
                        opt_value = opt.get_attribute("value") or ""
                        if (
                                normalized_answer in opt_text or opt_text in normalized_answer or normalized_answer == opt_value.lower()):
                            field.select_option(opt_value)
                            print(f"Selected dropdown: '{opt_text}' (value: {opt_value})")
                            matched = True
                            break

                    if not matched:
                        print(f"No dropdown option matched: '{answer}'")
                elif tag == "textarea":
                    field.fill(answer)
                    print(f"Filled textarea with: {answer}")
                else:
                    print(f"Unsupported tag: {tag}")
        except Exception as e:
            print(f"Error processing field '{label_text}': {e}")

    def process_fields_in_modal():
        try:
            modal = page.query_selector("div.jobs-easy-apply-modal")
            if not modal:
                print("Easy Apply modal not found.")
                return False
            # Label-associated fields
            labels = modal.query_selector_all("label")
            for label in labels:
                label_text = label.inner_text().strip()
                if not label_text or label_text in seen:
                    continue
                seen.add(label_text)
                # Try 'for' attribute
                for_attr = label.get_attribute("for")
                field = None
                if for_attr:
                    field = modal.query_selector(f"#{for_attr}")
                if not field:
                    field = label.query_selector("input, select, textarea") or label.evaluate_handle("el => el.nextElementSibling")

                if field:
                    print(f"Label: {label_text}")
                    fill_field(field, label_text)

            # Fields with aria-label or placeholder
            other_fields = modal.query_selector_all("input, select, textarea")
            for field in other_fields:
                if not field.is_enabled():
                    continue
                attr = field.get_attribute("aria-label") or field.get_attribute("placeholder")
                if attr and attr.strip() not in seen:
                    seen.add(attr.strip())
                    print(f"Field: {attr.strip()}")
                    fill_field(field, attr.strip())
            return True
        except Exception as e:
            print(f"Error in modal field processing: {e}")
            return False
    process_fields_in_modal()
    while True:
        try:
            next_button = page.locator(
                "button:has-text('Next'), button:has-text('Review'), button:has-text('Submit')"
            ).first
            if not next_button or not next_button.is_enabled():
                print("No enabled Next/Review/Submit button.")
                return
            btn_text = next_button.inner_text().strip()
            print(f"\nClicking: {btn_text}")
            next_button.click()
            page.wait_for_timeout(2000)  # Give page time to update
            if btn_text.lower() == "submit":
                print("Submitted. Looking for Done...")
                try:
                    #Wait for Done/Close/Back to search button to appear
                    done_span = page.locator(
                        "span:has-text('Done'), span:has-text('Close'), span:has-text('Back to search')"
                    ).first
                    done_span.wait_for(state="visible", timeout=7000)
                    done_button = done_span.locator("xpath=ancestor::button[1]")

                    if done_button.is_visible() and done_button.is_enabled():
                        done_button.click()
                        print("Clicked 'Done' button successfully.")
                    else:
                        print("Done not clickable. Forcing JS click.")
                        page.evaluate("btn => btn.click()", done_button)

                    #Wait for modal to disappear (not required, but safe)
                    try:
                        page.wait_for_selector("div.jobs-easy-apply-modal", state="detached", timeout=5000)
                        print("Modal closed.")
                    except:
                        print("Modal may already be closed.")
                except Exception as e:
                    print(f"Done button failed: {e}")
                return  # Go to next job
            # Process only intermediate steps
            modal = page.query_selector("div.jobs-easy-apply-modal")
            if not modal:
                print("Easy Apply modal not found. Exiting form.")
                return qna_pairs
            process_fields_in_modal()

        except Exception as e:
            print(f"Navigation failed: {e}")
            return qna_pairs

def filter_easy_apply_jobs(page,file_id,manual_answers):
    # form_labels = extract_all_form_labels_across_steps(page)
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
    jobs_applied_count = 0
    for job in jobs:
        if jobs_applied_count >= MAX_JOBS_PER_RUN:
            break
    # for idx, job in enumerate(jobs):
    #     if idx >= MAX_JOBS_PER_RUN:
    #         break
        try:
            job.click()
            page.wait_for_timeout(3000)
            # Skip already applied jobs (check badge or status)
            if page.query_selector("span:has-text('Applied')") or page.query_selector(
                    "span:has-text('Already applied')"):
                print("Already applied — skipping this job.")
                continue
            # Skip if not Easy Apply
            apply_btn = page.query_selector("button.jobs-apply-button")
            if not apply_btn:
                print("Skipping non-Easy Apply job")
                continue
            # --- Job Info Extraction ---
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
            job_description = (
                page.query_selector("div.job-details-module.jobs-description")
            )

            title_text = job_title.inner_text().strip() if job_title else "N/A"
            company_text = company_name.inner_text().strip() if company_name else "N/A"
            location_text = location.inner_text().strip() if location else "N/A"
            desc_text = job_description.inner_text().strip() if job_description else "N/A"

            # --- Apply Process ---
            apply_btn.click()
            page.wait_for_timeout(2000)
            qna_pairs = extract_and_fill_form_fields_across_steps(page, file_id, manual_answers)
            fill_easy_apply_form_with_llm(page, file_id, manual_answers)
            log_application_data(title_text, company_text, location_text, desc_text, qna_pairs)
            page.wait_for_timeout(2000)
            # --- Submit / Close Form Logic ---
            done_button = page.query_selector(
                "button:has-text('Done'), button:has-text('Close'), button:has-text('Back to search')")
            next_btn = page.query_selector("button:has-text('Next')")
            review_btn = page.query_selector("button:has-text('Review')")
            submit_btn = page.query_selector("button:has-text('Submit')")

            if done_button and done_button.is_enabled():
                done_button.click()
                print("Clicked Done/Close button.")
                page.wait_for_selector("div.jobs-easy-apply-modal", state="detached", timeout=8000)
            elif submit_btn and submit_btn.is_enabled():
                submit_btn.click()
                print("Submitted application.")
                page.wait_for_timeout(4000)
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
                break

            # Add to applied list and increment counter
            applied_jobs.append({
                "Job Title": title_text,
                "Company Name": company_text,
                "Location": location_text,
                "Job Description": desc_text,
            })

            jobs_applied_count += 1
            print(f"Applied to {jobs_applied_count}/{MAX_JOBS_PER_RUN}")
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Error in job: {e}")
            # print(f"Error in job #{idx + 1}: {e}")
            continue

    save_to_csv(applied_jobs)
    print(f"Total jobs applied: {len(applied_jobs)} out of max {MAX_JOBS_PER_RUN}")

# def filter_easy_apply_jobs(page, file_id, manual_answers):
#     applied_jobs = []
#     jobs_applied_count = 0
#
#     try:
#         filter_btn = page.locator("button:has-text('Easy Apply')").first
#         filter_btn.click()
#         print("Filtered to Easy Apply jobs")
#         page.wait_for_timeout(3000)
#     except Exception as e:
#         print("Easy Apply filter error:", e)
#
#     while jobs_applied_count < MAX_JOBS_PER_RUN:
#         page.wait_for_selector("div.job-card-container", timeout=10000)
#         jobs = page.query_selector_all("div.job-card-container")
#
#         for job in jobs:
#             # Scroll job list container to load more jobs
#             try:
#                 job_list_container = page.query_selector("div.jobs-search-results-list")
#                 if job_list_container:
#                     page.evaluate("""
#                         el => {
#                             el.scrollBy({ top: el.scrollHeight, behavior: 'smooth' });
#                         }
#                     """, job_list_container)
#                     print("Scrolled job list to load more jobs...")
#                     page.wait_for_timeout(3000)
#                 else:
#                     print("Job list container not found.")
#             except Exception as e:
#                 print(f"Failed to scroll job list: {e}")
#
#             if jobs_applied_count >= MAX_JOBS_PER_RUN:
#                 break
#             try:
#                 job.scroll_into_view_if_needed()
#                 job.click()
#                 page.wait_for_timeout(3000)
#
#                 if page.query_selector("span:has-text('Applied')") or page.query_selector("span:has-text('Already applied')"):
#                     print("Already applied — skipping this job.")
#                     continue
#
#                 apply_btn = page.query_selector("button.jobs-apply-button")
#                 if not apply_btn:
#                     print("Skipping non-Easy Apply job")
#                     continue
#
#                 job_title = page.query_selector("h2.topcard__title") or page.query_selector("h1")
#                 company_name = (
#                     page.query_selector("a.topcard__org-name-link") or
#                     page.query_selector("span.topcard__flavor") or
#                     page.query_selector("div.artdeco-entity-lockup__subtitle")
#                 )
#                 location = (
#                     page.query_selector("span.jobs-unified-top-card__bullet") or
#                     page.query_selector("span.topcard__flavor--bullet") or
#                     page.query_selector("div.artdeco-entity-lockup__caption")
#                 )
#                 job_description = page.query_selector("div.job-details-module.jobs-description")
#
#                 title_text = job_title.inner_text().strip() if job_title else "N/A"
#                 company_text = company_name.inner_text().strip() if company_name else "N/A"
#                 location_text = location.inner_text().strip() if location else "N/A"
#                 desc_text = job_description.inner_text().strip() if job_description else "N/A"
#
#                 apply_btn.click()
#                 page.wait_for_timeout(2000)
#
#                 qna_pairs = extract_and_fill_form_fields_across_steps(page, file_id, manual_answers)
#                 fill_easy_apply_form_with_llm(page, file_id, manual_answers)
#                 log_application_data(title_text, company_text, location_text, desc_text, qna_pairs)
#
#                 page.wait_for_timeout(2000)
#
#                 done_button = page.query_selector("button:has-text('Done'), button:has-text('Close'), button:has-text('Back to search')")
#                 if done_button and done_button.is_enabled():
#                     done_button.click()
#                     print("Clicked Done/Close button.")
#                     page.wait_for_selector("div.jobs-easy-apply-modal", state="detached", timeout=8000)
#
#                 applied_jobs.append({
#                     "Job Title": title_text,
#                     "Company Name": company_text,
#                     "Location": location_text,
#                     "Job Description": desc_text,
#                 })
#                 jobs_applied_count += 1
#                 print(f"✅ Applied to {jobs_applied_count}/{MAX_JOBS_PER_RUN}")
#                 page.wait_for_timeout(3000)
#
#             except Exception as e:
#                 print(f"❌ Error in job: {e}")
#                 continue
#
#         # Check for next pagination button
#         next_button = page.locator("button[aria-label='Next']").first
#         if next_button and next_button.is_enabled():
#             try:
#                 print("🔁 Moving to next page of job listings...")
#                 next_button.click()
#                 page.wait_for_timeout(5000)
#             except Exception as e:
#                 print(f"⚠️ Failed to click next page: {e}")
#                 break
#         else:
#             print("❌ No next page button found or it's disabled.")
#             break
#
#     save_to_csv(applied_jobs)
#     print(f"🏁 Total jobs applied: {len(applied_jobs)} out of max {MAX_JOBS_PER_RUN}")


# def filter_easy_apply_jobs(page, file_id, manual_answers):
#     applied_jobs = []
#     jobs_applied_count = 0
#
#     try:
#         filter_btn = page.locator("button:has-text('Easy Apply')").first
#         filter_btn.click()
#         print("Filtered to Easy Apply jobs")
#         page.wait_for_timeout(3000)
#     except Exception as e:
#         print("Easy Apply filter error:", e)
#
#     while jobs_applied_count < MAX_JOBS_PER_RUN:
#         page.wait_for_selector("div.job-card-container", timeout=10000)
#         jobs = page.query_selector_all("div.job-card-container")
#
#         for job in jobs:
#             if jobs_applied_count >= MAX_JOBS_PER_RUN:
#                 break
#
#             try:
#                 job.scroll_into_view_if_needed()
#                 job.click()
#                 page.wait_for_timeout(3000)
#
#                 if page.query_selector("span:has-text('Applied')") or page.query_selector("span:has-text('Already applied')"):
#                     print("Already applied — skipping this job.")
#                     continue
#
#                 apply_btn = page.query_selector("button.jobs-apply-button")
#                 if not apply_btn:
#                     print("Skipping non-Easy Apply job")
#                     continue
#
#                 job_title = page.query_selector("h2.topcard__title") or page.query_selector("h1")
#                 company_name = (
#                     page.query_selector("a.topcard__org-name-link") or
#                     page.query_selector("span.topcard__flavor") or
#                     page.query_selector("div.artdeco-entity-lockup__subtitle")
#                 )
#                 location = (
#                     page.query_selector("span.jobs-unified-top-card__bullet") or
#                     page.query_selector("span.topcard__flavor--bullet") or
#                     page.query_selector("div.artdeco-entity-lockup__caption")
#                 )
#                 job_description = page.query_selector("div.job-details-module.jobs-description")
#
#                 title_text = job_title.inner_text().strip() if job_title else "N/A"
#                 company_text = company_name.inner_text().strip() if company_name else "N/A"
#                 location_text = location.inner_text().strip() if location else "N/A"
#                 desc_text = job_description.inner_text().strip() if job_description else "N/A"
#
#                 apply_btn.click()
#                 page.wait_for_timeout(2000)
#
#                 qna_pairs = extract_and_fill_form_fields_across_steps(page, file_id, manual_answers)
#                 fill_easy_apply_form_with_llm(page, file_id, manual_answers)
#                 log_application_data(title_text, company_text, location_text, desc_text, qna_pairs)
#
#                 page.wait_for_timeout(2000)
#
#                 done_button = page.query_selector("button:has-text('Done'), button:has-text('Close'), button:has-text('Back to search')")
#                 if done_button and done_button.is_enabled():
#                     done_button.click()
#                     print("Clicked Done/Close button.")
#                     page.wait_for_selector("div.jobs-easy-apply-modal", state="detached", timeout=8000)
#
#                 applied_jobs.append({
#                     "Job Title": title_text,
#                     "Company Name": company_text,
#                     "Location": location_text,
#                     "Job Description": desc_text,
#                 })
#                 jobs_applied_count += 1
#                 print(f"✅ Applied to {jobs_applied_count}/{MAX_JOBS_PER_RUN}")
#                 page.wait_for_timeout(3000)
#
#
#             except Exception as e:
#                 print(f"❌ Error in job: {e}")
#                 continue
#
#
#     save_to_csv(applied_jobs)
#     print(f"🏁 Total jobs applied: {len(applied_jobs)} out of max {MAX_JOBS_PER_RUN}")



def save_to_csv(data, filename="application_log.csv"):
    job_count = len(data)
    file_exists = os.path.isfile(filename)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Applied Job Count"])
        writer.writerow([timestamp, job_count])


def fill_easy_apply_form_with_llm(page, file_id, manual_answers):
    try:
        modal = page.wait_for_selector("div.jobs-easy-apply-modal", timeout=7000)
    except Exception:
        print(" ..Easy Apply modal did not appear.")
        return
    # Get all labels inside the modal
    labels = modal.query_selector_all("label, span, p")  # broaden span/p if labels are inside those

    for label in labels:
        label_text = label.inner_text().strip()
        if not label_text:
            continue
        print(f"Question: {label_text}")
        # Ask LLM for answer based on the label text question
        # answer = get_answer_from_llm(label_text, file_id).strip()
        answer = get_answer_from_llm(label_text, file_id, manual_answers).strip()
        print(f"Answer from LLM: {answer}")
        # Find related input element:
        input_id = label.get_attribute("for")
        input_elem = None
        if input_id:
            input_elem = page.query_selector(f"#{input_id}")
        else:
            # fallback: try to find input/select/textarea near label
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
        manual_answers = load_manual_answers()  # Add this line

        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        login_to_linkedin(page)
        search_jobs(page)
        file_id = upload_resume_get_file_id(RESUME_PATH)  # <- Get file ID here
        # file_id = None  # Skipping resume upload due to server error
        filter_easy_apply_jobs(page, file_id, manual_answers)
        browser.close()

if __name__ == "__main__":
    main()
