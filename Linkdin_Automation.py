####### Print Label and There answer into application_log.csv file ####################

from datetime import datetime
import time
import json
import csv
import os
import requests
from playwright.sync_api import sync_playwright

#Load config.json
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
                f"If the question is about eligibility (Yes/No), always answer either 'Yes' or 'No'.\n"
                f"Only return '0' for numeric experience questions.\n"
                f"If the question asks about years of experience with a specific skill or technology "
                f"(e.g., Angular, Node.js), extract that number from the resume if present. "
                f"Return a whole number between 0 and 30. If it's not mentioned, return 0.\n"
                f"If the question is about eligibility (Yes/No), answer only Yes or No.\n"
                f"If unsure, answer 0 for years or No for eligibility.\n\n"
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
    return response.json()['choices'][0]['message']['content']

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

def extract_and_fill_form_fields_across_steps(page, file_id):
    print("\n📋 Extracting and filling form fields from all steps:")
    seen = set()
    qna_pairs = []

    def fill_field(field, label_text):
        try:
            tag = field.evaluate("el => el.tagName.toLowerCase()")
            input_type = field.get_attribute("type") or ""
            answer = None
            is_prefilled = False

            # ✅ Check if field already has value
            if tag == "input":
                if input_type == "checkbox":
                    if field.is_checked():
                        print(f"⏭️ Skipping already selected checkbox: {label_text}")
                        answer = "Already selected"
                        is_prefilled = True
                else:
                    current_value = field.input_value().strip()
                    if current_value:
                        print(f"⏭️ Skipping already filled input: {label_text}")
                        answer = current_value
                        is_prefilled = True

            # elif tag == "select":
            #     selected_option = field.query_selector("option:checked")
            #     selected_text = selected_option.inner_text().strip() if selected_option else ""
            #     if selected_text.lower() not in ["", "select", "choose", "none", "n/a"]:
            #         print(f"⏭️ Skipping already selected dropdown: {label_text} (value: '{selected_text}')")
            #         answer = selected_text
            #         is_prefilled = True
            elif tag == "select":

                try:

                    selected_option = field.query_selector("option:checked")

                    selected_text = selected_option.inner_text().strip().lower() if selected_option else ""

                    # Only skip if it's a real selection, not a placeholder

                    if selected_text not in ["", "select", "select an option", "choose", "choose an option", "none",
                                             "n/a"]:

                        print(f"⏭️ Skipping already selected dropdown: {label_text} (value: '{selected_text}')")

                        return

                    else:

                        print(f"🟡 Will fill dropdown for: {label_text} (current value: '{selected_text}')")

                except Exception as e:

                    print(f"⚠️ Error checking dropdown value: {e}")



            elif tag == "select":

                try:

                    # STEP 1: Skip if already selected with real value

                    selected_option = field.query_selector("option:checked")

                    selected_text = selected_option.inner_text().strip().lower() if selected_option else ""

                    if selected_text not in ["", "select", "select an option", "choose", "choose an option", "none",
                                             "n/a"]:

                        print(f"⏭️ Skipping already selected dropdown: {label_text} (value: '{selected_text}')")

                        return

                    else:

                        print(f"🟡 Will fill dropdown for: {label_text} (current value: '{selected_text}')")

                    # STEP 2: Match the LLM answer to dropdown options

                    options = field.query_selector_all("option")

                    normalized_answer = answer.lower().strip()

                    # 🔁 Fix: Convert '0' to 'no' if options include Yes/No

                    option_texts = [opt.inner_text().strip().lower() for opt in options]

                    if normalized_answer == "0" and "yes" in option_texts and "no" in option_texts:
                        print("🔁 Interpreting '0' as 'No' for Yes/No dropdown")

                        normalized_answer = "no"

                    matched = False

                    for opt in options:

                        opt_text = opt.inner_text().strip().lower()

                        opt_value = opt.get_attribute("value") or ""

                        if normalized_answer in opt_text or opt_text in normalized_answer:
                            field.select_option(opt_value)

                            print(f"✅ Matched and selected dropdown option: {opt_text} ({opt_value})")

                            matched = True

                            break

                    if not matched:
                        print(f"❌ No matching dropdown option found for: '{answer}'")

                except Exception as e:

                    print(f"❌ Failed to select dropdown option '{answer}': {e}")

            elif tag == "textarea":
                current_value = field.input_value().strip()
                if current_value:
                    print(f"⏭️ Skipping already filled textarea: {label_text}")
                    answer = current_value
                    is_prefilled = True

            # ✅ If not prefilled, call LLM to get answer
            if not is_prefilled:
                answer = get_answer_from_llm(label_text, file_id).strip()
                print(f"📝 Filled using LLM → Q: {label_text} | A: {answer}")

            else:
                print(f"📌 Used existing value → Q: {label_text} | A: {answer}")

            # ✅ Log the label and answer (always)
            qna_pairs.append((label_text, answer))

            # ✅ Only fill if not already filled
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
                                    print(f"✅ Clicked checkbox: '{label}'")
                                    matched = True
                                    break
                            except Exception as e:
                                print(f"⚠️ Error clicking checkbox option: {e}")
                        if not matched:
                            print(f"❌ No checkbox match for: '{answer}'")
                    else:
                        field.fill(answer)
                        print(f"✅ Filled input with: {answer}")


                elif tag == "select":

                    options = field.query_selector_all("option")

                    matched = False

                    for opt in options:

                        opt_text = opt.inner_text().strip().lower()

                        opt_value = opt.get_attribute("value")

                        if answer.lower() in opt_text or answer.lower() == opt_value.lower():
                            field.select_option(opt_value)

                            print(f"✅ Selected dropdown: {opt_text}")

                            matched = True

                            break

                    if not matched:
                        print(f"❌ No dropdown option matched: {answer}")
                elif tag == "textarea":
                    field.fill(answer)
                    print(f"✅ Filled textarea with: {answer}")

                else:
                    print(f"⚠️ Unsupported tag: {tag}")

        except Exception as e:
            print(f"❌ Error processing field '{label_text}': {e}")

    def process_fields_in_modal():
        try:
            modal = page.query_selector("div.jobs-easy-apply-modal")
            if not modal:
                print("❌ Easy Apply modal not found.")
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
                    print(f"🔹 Label: {label_text}")
                    fill_field(field, label_text)

            # Fields with aria-label or placeholder
            other_fields = modal.query_selector_all("input, select, textarea")
            for field in other_fields:
                if not field.is_enabled():
                    continue
                attr = field.get_attribute("aria-label") or field.get_attribute("placeholder")
                if attr and attr.strip() not in seen:
                    seen.add(attr.strip())
                    print(f"🔸 Field: {attr.strip()}")
                    fill_field(field, attr.strip())

            return True
        except Exception as e:
            print(f"❌ Error in modal field processing: {e}")
            return False

    process_fields_in_modal()

    while True:
        try:
            next_button = page.locator(
                "button:has-text('Next'), button:has-text('Review'), button:has-text('Submit')"
            ).first

            if not next_button or not next_button.is_enabled():
                print("❌ No enabled Next/Review/Submit button.")
                return

            btn_text = next_button.inner_text().strip()
            print(f"\n➡️ Clicking: {btn_text}")
            next_button.click()
            page.wait_for_timeout(2000)  # ⏳ Give page time to update

            if btn_text.lower() == "submit":
                print("✅ Submitted. Looking for Done...")

                try:
                    # ✅ Wait for Done/Close/Back to search button to appear
                    done_span = page.locator(
                        "span:has-text('Done'), span:has-text('Close'), span:has-text('Back to search')"
                    ).first
                    done_span.wait_for(state="visible", timeout=7000)
                    done_button = done_span.locator("xpath=ancestor::button[1]")

                    if done_button.is_visible() and done_button.is_enabled():
                        done_button.click()
                        print("🎉 Clicked 'Done' button successfully.")
                    else:
                        print("⚠️ Done not clickable. Forcing JS click.")
                        page.evaluate("btn => btn.click()", done_button)

                    # ✅ Wait for modal to disappear (not required, but safe)
                    try:
                        page.wait_for_selector("div.jobs-easy-apply-modal", state="detached", timeout=5000)
                        print("✅ Modal closed.")
                    except:
                        print("⚠️ Modal may already be closed.")

                except Exception as e:
                    print(f"❌ Done button failed: {e}")

                return  # ✅ Go to next job

            # ✅ Process only intermediate steps
            modal = page.query_selector("div.jobs-easy-apply-modal")
            if not modal:
                print("❌ Easy Apply modal not found. Exiting form.")
                return qna_pairs


            process_fields_in_modal()

        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return qna_pairs


def filter_easy_apply_jobs(page,file_id):
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
    for idx, job in enumerate(jobs):
        if idx >= MAX_JOBS_PER_RUN:
            break
        try:
            job.click()
            page.wait_for_timeout(3000)
            apply_btn = page.query_selector("button.jobs-apply-button")
            if not apply_btn:
                print("Skipping non-Easy Apply job")

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

            # job_description = page.query_selector("div.description__text")
            job_description = (
                page.query_selector("div.job-details-module.jobs-description")
            )

            title_text = job_title.inner_text().strip() if job_title else "N/A"
            company_text = company_name.inner_text().strip() if company_name else "N/A"
            location_text = location.inner_text().strip() if location else "N/A"
            desc_text = job_description.inner_text().strip() if job_description else "N/A"
            apply_btn.click()
            page.wait_for_timeout(2000)
            qna_pairs = extract_and_fill_form_fields_across_steps(page, file_id)
            fill_easy_apply_form_with_llm(page, file_id)
            log_application_data(title_text, company_text, location_text, desc_text, qna_pairs)
            page.wait_for_timeout(3000)

            # while True:
            page.wait_for_timeout(1000)
            done_button = page.query_selector("button:has-text('Done'), button:has-text('Close'), button:has-text('Back to search')")
            next_btn = page.query_selector("button:has-text('Next')")
            review_btn = page.query_selector("button:has-text('Review')")
            submit_btn = page.query_selector("button:has-text('Submit')")

            if done_button and done_button.is_enabled():
                    try:
                        done_button.click()
                        print("✅ Clicked Done/Close button.")
                        page.wait_for_selector("div.jobs-easy-apply-modal", state="detached", timeout=8000)
                        print("✅ Modal closed, ready to move to next job.")
                        # continue  # Go to next job in loop
                    except Exception as e:
                        print(f"❌ Failed to click Done/Close: {e}")
                        page.screenshot(path="done_button_error.png")


            elif submit_btn and submit_btn.is_enabled():
                    submit_btn.click()
                    print("✅ Submitted application.")
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
    print(f"✅ Total jobs applied: {len(applied_jobs)} out of max {MAX_JOBS_PER_RUN}")

def save_to_csv(data, filename="application_log.csv"):
    job_count = len(data)
    file_exists = os.path.isfile(filename)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Applied Job Count"])
        writer.writerow([timestamp, job_count])


def fill_easy_apply_form_with_llm(page, file_id):
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
        answer = get_answer_from_llm(label_text, file_id).strip()
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
                    print(f"  ⚠️ No matching option for '{answer}' in select dropdown: {label_text}")

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


