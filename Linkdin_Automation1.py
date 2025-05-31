#
# import json
# import csv
# import os
# import requests
# from playwright.sync_api import sync_playwright
#
# #Load config.json
# with open("config.json", "r") as f:
#     config = json.load(f)
#
# LINKEDIN_USERNAME = config["LINKEDIN_USERNAME"]
# LINKEDIN_PASSWORD = config["LINKEDIN_PASSWORD"]
# RESUME_PATH = config["resume_path"]
# TARGET_JOB_TITLE = config["target_job_title"]
# TARGET_LOCATION = config["target_location"]
# LOG_FILE_PATH = config["log_file_path"]
# OPENWEBUI_API = config["OPENWEBUI_API_URL"]
# OPENWEBUI_MODEL = config["OPENWEBUI_MODEL"]
# MAX_JOBS_PER_RUN = config.get("max_jobs_per_run", 5)
# api_token = config["OPENWEBUI_API_KEY"]
#
# # def ask_llm(prompt):
# #     payload = {
# #         "model": OLLAMA_MODEL,
# #         "prompt": prompt,
# #         "stream": False
# #     }
# #
# #     print(f"Sending request to {OLLAMA_API_URL} with payload: {payload}")
# #
# #     try:
# #         response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
# #         if response.status_code == 200:
# #             data = response.json()
# #             print(f"LLM Response: {data}")
# #             return data.get("response", "").strip()
# #         else:
# #             print(f"LLM Error {response.status_code}: {response.text}")
# #             return ""
# #     except Exception as e:
# #         print(f"Error contacting LLM: {e}")
# #         return ""
#
# def load_resume():
#     with open("resume.txt", "r", encoding="utf-8") as f:
#         return f.read()
#
#
#
# # def get_answer_from_llm(question, resume_data):
# #     payload = {
# #         "model": "gemma3",
# #         "prompt": f"Answer this job application field briefly and professionally: '{question}'. Use this resume info:\n\n{resume_data}",
# #         "stream": False
# #     }
# #     print(f"\nSending to LLM ➤ {question}")
# #     try:
# #         res = requests.post("https://owui.codersboutique.com/api/chat/completions", json=payload, timeout=30)
# #         res.raise_for_status()
# #         answer = res.json()["response"]
# #         print(f"💡 Answer: {answer}")
# #         return answer
# #     except Exception as e:
# #         print("❌ LLM Error:", e)
# #         return ""
#
# def get_answer_from_llm(question: str,resume_data) -> str:
#
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {api_token}"
#     }
#
#     payload = {
#         "model": "gemma3",  # You can adjust this if needed
#         "messages": [
#             {"role": "user", "content": question}
#         ]
#     }
#
#     try:
#         response = requests.post(OPENWEBUI_API, headers=headers, json=payload)
#         response.raise_for_status()
#         data = response.json()
#         return data["choices"][0]["message"]["content"].strip()
#     except requests.exceptions.RequestException as e:
#         print(f"❌ LLM Error: {e}")
#         return ""
#     except Exception as e:
#         print(f"❌ Unexpected error: {e}")
#         return ""
# def login_to_linkedin(page):
#     page.goto("https://www.linkedin.com/login")
#     page.fill('input#username', LINKEDIN_USERNAME)
#     page.fill('input#password', LINKEDIN_PASSWORD)
#     page.click('button[type="submit"]')
#     try:
#         page.wait_for_url("https://www.linkedin.com/feed/", timeout=60000)
#         print("Logged in Successfully")
#     except:
#         page.screenshot(path="login_failed.png")
#         print("Login failed. Check credentials or captcha requirement.")
#         page.wait_for_timeout(10000)
#
# def search_jobs(page, job_title=TARGET_JOB_TITLE, job_location=TARGET_LOCATION):
#     page.goto("https://www.linkedin.com/jobs/")
#     if job_title:
#         try:
#             title_input = page.locator('//input[@aria-label="Search by title, skill, or company"]').first
#             title_input.wait_for(state="visible", timeout=20000)
#             title_input.click()
#             title_input.fill(job_title)
#             print("Entered Job Title")
#         except Exception as e:
#             print("Error entering job title:", e)
#     if job_location:
#         try:
#             location_input = page.locator('//input[@aria-label="City, state, or zip code"]').first
#             location_input.wait_for(state="visible", timeout=15000)
#             location_input.click()
#             location_input.press("Control+A")
#             location_input.press("Backspace")
#             location_input.fill(job_location)
#             page.wait_for_selector("ul[role='listbox'] li", timeout=5000)
#             page.keyboard.press("ArrowDown")
#             page.keyboard.press("Enter")
#             page.wait_for_timeout(5000)
#             print("Entered Job Location")
#         except Exception as e:
#             print("Error entering job location:", e)
#
#
# # def extract_all_form_labels_across_steps(page):
# #     print("\n📋 Extracting form labels/questions from all steps:")
# #     seen = set()
# #
# #     def extract_labels_from_modal():
# #         try:
# #             modal = page.query_selector("div.jobs-easy-apply-modal")
# #             if not modal:
# #                 print("❌ Easy Apply modal not found.")
# #                 return False
# #
# #             # Extract label elements
# #             labels = modal.query_selector_all("label")
# #             for label in labels:
# #                 text = label.inner_text().strip()
# #                 if text and text not in seen:
# #                     print(f"🔹 Label: {text}")
# #                     seen.add(text)
# #
# #             # Extract field placeholders or aria-labels
# #             fields = modal.query_selector_all("input, select, textarea")
# #             for field in fields:
# #                 attr = field.get_attribute("aria-label") or field.get_attribute("placeholder")
# #                 if attr and attr.strip() not in seen:
# #                     print(f"🔸 Field: {attr.strip()}")
# #                     seen.add(attr.strip())
# #
# #             return True
# #         except Exception as e:
# #             print(f"❌ Error extracting labels: {e}")
# #             return False
# #
# #     # Extract labels on the first step
# #     extract_labels_from_modal()
# #
# #     # Click through all form steps
# #     while True:
# #         try:
# #             # Find Next, Review, or Submit button
# #             next_button = page.locator(
# #                 "button:has-text('Next'), button:has-text('Review'), button:has-text('Submit')"
# #             ).first
# #
# #             if next_button.is_enabled():
# #                 btn_text = next_button.inner_text().strip()
# #                 print(f"\n➡️ Clicking: {btn_text} button")
# #                 next_button.click()
# #
# #                 # Wait for next step UI to load
# #                 page.wait_for_timeout(1500)
# #
# #                 # Extract new labels on this step
# #                 extract_labels_from_modal()
# #
# #                 if btn_text == "Submit":
# #                     print("✅ Reached final step (Submit).")
# #                     break
# #             else:
# #                 print("❌ No further step buttons enabled.")
# #                 break
# #         except Exception as e:
# #             print(f"❌ Could not proceed to next step: {e}")
# #             break
#
#
# def filter_easy_apply_jobs(page):
#     applied_jobs = []
#     try:
#         filter_btn = page.locator("button:has-text('Easy Apply')").first
#         filter_btn.click()
#
#         print("Filtered to Easy Apply jobs")
#         page.wait_for_timeout(3000)
#     except Exception as e:
#         print("Easy Apply filter error:", e)
#     page.wait_for_selector("div.job-card-container", timeout=10000)
#     jobs = page.query_selector_all("div.job-card-container")
#     for idx, job in enumerate(jobs):
#         if idx >= MAX_JOBS_PER_RUN:
#             break
#         try:
#             job.click()
#             page.wait_for_timeout(3000)
#             apply_btn = page.query_selector("button.jobs-apply-button")
#             if not apply_btn:
#                 print("Skipping non-Easy Apply job")
#                 continue
#             job_title = page.query_selector("h2.topcard__title") or page.query_selector("h1")
#
#             company_name = (
#                     page.query_selector("a.topcard__org-name-link") or
#                     page.query_selector("span.topcard__flavor") or
#                     page.query_selector("div.artdeco-entity-lockup__subtitle")
#             )
#             location = (
#                     page.query_selector("span.jobs-unified-top-card__bullet") or
#                     page.query_selector("span.topcard__flavor--bullet") or
#                     page.query_selector("div.artdeco-entity-lockup__caption")
#             )
#             job.click()
#             page.wait_for_timeout(5000)
#
#             right_panel = page.query_selector("div.jobs-details") or page.query_selector("div.jobs-search__job-details")
#             if right_panel:
#                 right_panel.scroll_into_view_if_needed()
#                 page.mouse.wheel(0, 5000)
#                 page.wait_for_timeout(2000)
#
#             # job_description = page.query_selector("div.description__text")
#             job_description = (
#                 page.query_selector("div.job-details-module.jobs-description")
#             )
#
#             title_text = job_title.inner_text().strip() if job_title else "N/A"
#             company_text = company_name.inner_text().strip() if company_name else "N/A"
#             location_text = location.inner_text().strip() if location else "N/A"
#             desc_text = job_description.inner_text().strip() if job_description else "N/A"
#             apply_btn.click()
#             page.wait_for_timeout(2000)
#
#             # get_easy_apply_form_labels(page)
#             # extract_all_form_labels_across_steps(page)
#
#             while True:
#                 page.wait_for_timeout(1000)
#                 fill_all_fields_on_page(page)
#                 next_btn = page.query_selector("button:has-text('Next')")
#                 review_btn = page.query_selector("button:has-text('Review')")
#                 submit_btn = page.query_selector("button:has-text('Submit')")
#                 if submit_btn and submit_btn.is_enabled():
#                     submit_btn.click()
#                     print("Application Submitted!")
#                     page.wait_for_timeout(3000)
#                     try:
#                         done_button = page.locator("button:has-text('Done')")
#                         done_button.wait_for(timeout=5000)
#                         done_button.click()
#                         print("Clicked 'Done'")
#                     except Exception as e:
#                         print("Done button not found or error:", e)
#                     break
#                 elif review_btn and review_btn.is_enabled():
#                     review_btn.click()
#                     print("Reviewing Application...")
#                     page.wait_for_timeout(2000)
#                 elif next_btn and next_btn.is_enabled():
#                     next_btn.click()
#                     print("Moving to next step...")
#                     page.wait_for_timeout(2000)
#                 else:
#                     print("No further steps.")
#                     break
#             applied_jobs.append({
#                 "Job Title": title_text,
#                 "Company Name": company_text,
#                 "Location": location_text,
#                 "Job Description": desc_text,
#             })
#             page.wait_for_timeout(3000)
#         except Exception as e:
#             print(f"Error in job #{idx + 1}: {e}")
#             continue
#     save_to_csv(applied_jobs)
#     print(f"Total jobs applied: {len(applied_jobs)}")
#
# def save_to_csv(data, filename="application_log.csv"):
#     file_exists = os.path.isfile(filename)
#     with open(filename, mode='a', newline='', encoding='utf-8') as file:
#         writer = csv.DictWriter(file, fieldnames=["Job Title", "Company Name", "Location", "Job Description"])
#         if not file_exists:
#             writer.writeheader()
#         for row in data:
#             writer.writerow(row)
#
# # def fill_all_fields_on_page(page):
# #     # file_inputs = page.query_selector_all("input[type='file']")
# #     # for file_input in file_inputs:
# #     #     try:
# #     #         file_input.set_input_files(RESUME_PATH)
# #     #         print(f"\ud83d\udcce Uploaded resume: {RESUME_PATH}")
# #     #     except Exception as e:
# #     #         print(f"Resume upload failed: {e}")
# #
# #
# #     text_fields = page.query_selector_all("input:not([type=hidden]):not([readonly]), textarea")
# #     for field in text_fields:
# #         try:
# #             label = field.evaluate("el => el.closest('label')?.innerText || el.closest('div')?.innerText || ''")
# #             if label:
# #                 question = f"Answer this job application field briefly and professionally: '{label}'"
# #                 answer = get_answer_from_llm(question,resume_data)
# #                 if answer:
# #                     print(f"Filling '{label}' with: {answer}")
# #                     field.fill(answer)
# #         except Exception as e:
# #             print(f"Error filling text field: {e}")
#
#
# #     dropdowns = page.query_selector_all("select")
# #     for dropdown in dropdowns:
# #         try:
# #             label = dropdown.evaluate("el => el.closest('label')?.innerText || el.closest('div')?.innerText || ''")
# #             if label:
# #                 question = f"Select appropriate short answer for: '{label}' (must match dropdown option)"
# #                 answer = get_answer_from_llm(question,data)
# #                 if answer:
# #                     options = dropdown.query_selector_all("option")
# #                     for option in options:
# #                         if answer.lower() in option.inner_text().strip().lower():
# #                             dropdown.select_option(label=option.inner_text())
# #                             print(f"Selected '{answer}' for '{label}'")
# #                             break
# #         except Exception as e:
# #             print(f"Error selecting dropdown: {e}")
# #
# #
# #     comboboxes = page.query_selector_all('[role="combobox"]')
# #     for box in comboboxes:
# #         try:
# #             label = box.evaluate("el => el.closest('label')?.innerText || el.closest('div')?.innerText || ''")
# #             if label:
# #                 question = f"Provide a brief value for: '{label}'"
# #                 answer = get_answer_from_llm(question,resume_data)
# #                 if answer:
# #                     box.click()
# #                     page.keyboard.type(answer)
# #                     page.keyboard.press("Enter")
# #         except Exception as e:
# #             print(f"Error filling combobox: {e}")
# #     radio_buttons = page.query_selector_all('input[type="radio"]')
# #     for radio in radio_buttons:
# #         try:
# #             label = radio.evaluate("el => el.closest('label')?.innerText || ''")
# #             if label:
# #                 question = f"Should I select '{label}' in a job application? Answer Yes or No."
# #                 answer = get_answer_from_llm(question,resume_data)
# #                 if "yes" in answer.lower():
# #                     radio.check()
# #         except Exception as e:
# #             print(f"Error with radio button: {e}")
#
# def fill_all_fields_on_page(page):
#     resume_data = load_resume()
#
#     # Handle file uploads (resume)
#     file_inputs = page.query_selector_all("input[type='file']")
#     for file_input in file_inputs:
#         try:
#             file_input.set_input_files(RESUME_PATH)
#             print(f"📎 Uploaded resume: {RESUME_PATH}")
#         except Exception as e:
#             print(f"❌ Resume upload failed: {e}")
#
#     # Handle text and textarea fields
#     text_fields = page.query_selector_all("input:not([type=hidden]):not([readonly]), textarea")
#     for field in text_fields:
#         try:
#             label = field.evaluate("""
#                 el => {
#                     const labelEl = el.closest('label')?.innerText ||
#                                     el.parentElement?.querySelector('label')?.innerText ||
#                                     el.getAttribute('aria-label') ||
#                                     el.getAttribute('placeholder') ||
#                                     '';
#                     return labelEl.trim();
#                 }
#             """)
#             if not label:
#                 continue
#
#             answer = get_answer_from_llm(label, resume_data)
#             if answer:
#                 field.fill("")
#                 field.fill(answer)
#                 print(f"✍️ Filled: {label} => {answer}")
#         except Exception as e:
#             print(f"❌ Error filling field: {e}")
#
#     # Handle dropdowns
#     selects = page.query_selector_all("select")
#     for select in selects:
#         try:
#             label = select.evaluate("""
#                 el => {
#                     const labelEl = el.closest('label')?.innerText ||
#                                     el.parentElement?.querySelector('label')?.innerText ||
#                                     el.getAttribute('aria-label') ||
#                                     '';
#                     return labelEl.trim();
#                 }
#             """)
#             if not label:
#                 continue
#
#             answer = get_answer_from_llm(label, resume_data)
#             if answer:
#                 options = select.query_selector_all("option")
#                 matched = False
#                 for option in options:
#                     option_text = option.inner_text().strip().lower()
#                     if answer.strip().lower() in option_text or option_text in answer.strip().lower():
#                         value = option.get_attribute("value")
#                         select.select_option(value)
#                         print(f"🔽 Selected: {label} => {option_text}")
#                         matched = True
#                         break
#                 if not matched:
#                     print(f"⚠️ No matching option found for {label} => {answer}")
#         except Exception as e:
#             print(f"❌ Dropdown fill error: {e}")
#
#     # Handle radio buttons
#     radios = page.query_selector_all("input[type='radio']")
#     radio_groups = {}
#     for radio in radios:
#         name = radio.get_attribute("name")
#         if name not in radio_groups:
#             radio_groups[name] = []
#         radio_groups[name].append(radio)
#
#     for group_name, group_radios in radio_groups.items():
#         try:
#             label = group_radios[0].evaluate("""
#                 el => {
#                     const container = el.closest('fieldset') || el.closest('div');
#                     return container?.innerText || '';
#                 }
#             """)
#             if not label:
#                 continue
#
#             answer = get_answer_from_llm(label, resume_data)
#             for radio in group_radios:
#                 value = radio.get_attribute("value") or radio.evaluate("el => el.labels?.[0]?.innerText || ''")
#                 if value and (answer.strip().lower() in value.strip().lower() or value.strip().lower() in answer.strip().lower()):
#                     radio.check()
#                     print(f"🔘 Checked: {label} => {value}")
#                     break
#         except Exception as e:
#             print(f"❌ Radio button error: {e}")
#
#
# def main():
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         page = browser.new_page()
#         login_to_linkedin(page)
#         search_jobs(page)
#         filter_easy_apply_jobs(page)
#         browser.close()
#
# if __name__ == "__main__":
#     main()
#
#




# print Label/Questions on application_log.csv

#
# import time
# import json
# import csv
# import os
# import requests
# from playwright.sync_api import sync_playwright
#
# #Load config.json
# with open("config.json", "r") as f:
#     config = json.load(f)
#
# LINKEDIN_USERNAME = config["LINKEDIN_USERNAME"]
# LINKEDIN_PASSWORD = config["LINKEDIN_PASSWORD"]
# RESUME_PATH = config["resume_path"]
# TARGET_JOB_TITLE = config["target_job_title"]
# TARGET_LOCATION = config["target_location"]
# LOG_FILE_PATH = config["log_file_path"]
# OPENWEBUI_API = config["OPENWEBUI_API_URL"]
# OPENWEBUI_MODEL = config["OPENWEBUI_MODEL"]
# MAX_JOBS_PER_RUN = config.get("max_jobs_per_run", 5)
# api_token = config["OPENWEBUI_API_KEY"]
#
#
# # def load_resume():
# #     with open("resume.txt", "r", encoding="utf-8") as f:
# #         return f.read()
# # print(load_resume())
#
# def load_resume():
#     resume_path = "C:/Users/ADMIN/PycharmProjects/PythonProject1/resume1.txt"
#
#     try:
#         with open(resume_path, "r", encoding="utf-8") as f:
#             resume_data = f.read()
#
#     # Optional: Print first 300 characters to confirm
#         print("🔍 Resume Data Loaded:\n", resume_data[:300])
#
#     except FileNotFoundError:
#         print(f"❌ File not found: {resume_path}")
#         resume_data = ""
#     except Exception as e:
#         print(f"❌ Error reading resume file: {e}")
#         resume_data = ""
# resume_data = load_resume()
#
#
#
#
# def log_application_data(job_title, company_name, location, description, form_labels):
#     log_file = 'application_log.csv'
#     file_exists = os.path.isfile(log_file)
#
#     with open(log_file, 'a', newline='', encoding='utf-8') as csvfile:
#         writer = csv.writer(csvfile)
#         if not file_exists:
#             writer.writerow([
#                 'Job Title',
#                 'Company Name',
#                 'Location',
#                 'Job Description',
#                 'form_labels'  # <-- Add this column
#             ])
#
#         writer.writerow([
#             job_title,
#             company_name,
#             location,
#             description,
#             form_labels,
#             ' | '.join(form_labels)  # <-- Join all label texts into a single string
#         ])
#
#
# # def get_answer_from_llm(label,resume_data) -> str:
# #
# #     headers = {
# #         "Content-Type": "application/json",
# #         "Authorization": f"Bearer {api_token}"
# #     }
# #
# #     payload = {
# #         "model": "gemma3",  # You can adjust this if needed
# #         "messages": [
# #             {"role": "user", "content": label}
# #         ]
# #     }
# #
# #     try:
# #         response = requests.post(OPENWEBUI_API, headers=headers, json=payload)
# #         response.raise_for_status()
# #         data = response.json()
# #         return data["choices"][0]["message"]["content"].strip()
# #     except requests.exceptions.RequestException as e:
# #         print(f"❌ LLM Error: {e}")
# #         return ""
# #     except Exception as e:
# #         print(f"❌ Unexpected error: {e}")
# #         return ""
#
# def get_answer_from_llm(question, file_id):
#     chat_headers = {
#         "Authorization": f"Bearer {api_token}",
#         "Accept": "application/json",
#         "Content-Type": "application/json"
#     }
#
#     payload = {
#         "model": OPENWEBUI_MODEL,
#         "messages": [
#             {"role": "user", "content": f"Answer this application question based on my resume: {question}"}
#         ],
#         "files": [{"type": "file", "id": file_id}]
#     }
#
#     response = requests.post(
#         f"{OPENWEBUI_API}",
#         headers=chat_headers,
#         json=payload
#     )
#
#     response.raise_for_status()
#     return response.json()['choices'][0]['message']['content']
#
# def login_to_linkedin(page):
#     page.goto("https://www.linkedin.com/login")
#     page.fill('input#username', LINKEDIN_USERNAME)
#     page.fill('input#password', LINKEDIN_PASSWORD)
#     page.click('button[type="submit"]')
#     try:
#         page.wait_for_url("https://www.linkedin.com/feed/", timeout=60000)
#         print("Logged in Successfully")
#     except:
#         page.screenshot(path="login_failed.png")
#         print("Login failed. Check credentials or captcha requirement.")
#         page.wait_for_timeout(10000)
#
# def search_jobs(page, job_title=TARGET_JOB_TITLE, job_location=TARGET_LOCATION):
#     page.goto("https://www.linkedin.com/jobs/")
#     if job_title:
#         try:
#             title_input = page.locator('//input[@aria-label="Search by title, skill, or company"]').first
#             title_input.wait_for(state="visible", timeout=20000)
#             title_input.click()
#             title_input.fill(job_title)
#             print("Entered Job Title")
#         except Exception as e:
#             print("Error entering job title:", e)
#     if job_location:
#         try:
#             location_input = page.locator('//input[@aria-label="City, state, or zip code"]').first
#             location_input.wait_for(state="visible", timeout=15000)
#             location_input.click()
#             location_input.press("Control+A")
#             location_input.press("Backspace")
#             location_input.fill(job_location)
#             page.wait_for_selector("ul[role='listbox'] li", timeout=5000)
#             page.keyboard.press("ArrowDown")
#             page.keyboard.press("Enter")
#             page.wait_for_timeout(5000)
#             print("Entered Job Location")
#         except Exception as e:
#             print("Error entering job location:", e)
#
#
# def extract_all_form_labels_across_steps(page):
#     print("\n📋 Extracting form labels/questions from all steps:")
#     seen = set()
#     collected_labels = []
#
#     def extract_labels_from_modal():
#         try:
#             modal = page.query_selector("div.jobs-easy-apply-modal")
#             if not modal:
#                 print("❌ Easy Apply modal not found.")
#                 return False
#
#             labels = modal.query_selector_all("label")
#             for label in labels:
#                 text = label.inner_text().strip()
#                 if text and text not in seen:
#                     print(f"🔹 Label: {text}")
#                     seen.add(text)
#                     collected_labels.append(text)
#
#             fields = modal.query_selector_all("input, select, textarea")
#             for field in fields:
#                 attr = field.get_attribute("aria-label") or field.get_attribute("placeholder")
#                 if attr and attr.strip() not in seen:
#                     print(f"🔸 Field: {attr.strip()}")
#                     seen.add(attr.strip())
#                     collected_labels.append(attr.strip())
#
#             return True
#         except Exception as e:
#             print(f"❌ Error extracting labels: {e}")
#             return False
#
#     extract_labels_from_modal()
#
#     while True:
#         try:
#             next_button = page.locator(
#                 "button:has-text('Next'), button:has-text('Review'), button:has-text('Submit')"
#             ).first
#
#             if next_button.is_enabled():
#                 btn_text = next_button.inner_text().strip()
#                 print(f"\n➡️ Clicking: {btn_text} button")
#                 next_button.click()
#                 page.wait_for_timeout(1500)
#                 extract_labels_from_modal()
#
#                 if btn_text == "Submit":
#                     print("✅ Reached final step (Submit).")
#                     break
#             else:
#                 print("❌ No further step buttons enabled.")
#                 break
#         except Exception as e:
#             print(f"❌ Could not proceed to next step: {e}")
#             break
#
#     return collected_labels
#
#

# def filter_easy_apply_jobs(page):
#     applied_jobs = []
#     try:
#         filter_btn = page.locator("button:has-text('Easy Apply')").first
#         filter_btn.click()
#
#         print("Filtered to Easy Apply jobs")
#         page.wait_for_timeout(3000)
#     except Exception as e:
#         print("Easy Apply filter error:", e)
#     page.wait_for_selector("div.job-card-container", timeout=10000)
#     jobs = page.query_selector_all("div.job-card-container")
#     for idx, job in enumerate(jobs):
#         if idx >= MAX_JOBS_PER_RUN:
#             break
#         try:
#             job.click()
#             page.wait_for_timeout(3000)
#             apply_btn = page.query_selector("button.jobs-apply-button")
#             if not apply_btn:
#                 print("Skipping non-Easy Apply job")
#                 continue
#             job_title = page.query_selector("h2.topcard__title") or page.query_selector("h1")
#
#             company_name = (
#                     page.query_selector("a.topcard__org-name-link") or
#                     page.query_selector("span.topcard__flavor") or
#                     page.query_selector("div.artdeco-entity-lockup__subtitle")
#             )
#             location = (
#                     page.query_selector("span.jobs-unified-top-card__bullet") or
#                     page.query_selector("span.topcard__flavor--bullet") or
#                     page.query_selector("div.artdeco-entity-lockup__caption")
#             )
#             job.click()
#             page.wait_for_timeout(5000)
#
#             right_panel = page.query_selector("div.jobs-details") or page.query_selector("div.jobs-search__job-details")
#             if right_panel:
#                 right_panel.scroll_into_view_if_needed()
#                 page.mouse.wheel(0, 5000)
#                 page.wait_for_timeout(2000)
#
#             # job_description = page.query_selector("div.description__text")
#             job_description = (
#                 page.query_selector("div.job-details-module.jobs-description")
#             )
#
#             title_text = job_title.inner_text().strip() if job_title else "N/A"
#             company_text = company_name.inner_text().strip() if company_name else "N/A"
#             location_text = location.inner_text().strip() if location else "N/A"
#             desc_text = job_description.inner_text().strip() if job_description else "N/A"
#             apply_btn.click()
#             page.wait_for_timeout(2000)
#
#             # get_easy_apply_form_labels(page)
#             # extract_all_form_labels_across_steps(page)
#             # log_application_data(job_title, company_name, location, job_description, form_labels)
#             form_labels = extract_all_form_labels_across_steps(page)
#             log_application_data(title_text, company_text, location_text, desc_text, form_labels)
#
#             while True:
#                 page.wait_for_timeout(1000)
#                 # fill_all_fields_on_page(page)
#                 next_btn = page.query_selector("button:has-text('Next')")
#                 review_btn = page.query_selector("button:has-text('Review')")
#                 submit_btn = page.query_selector("button:has-text('Submit')")
#                 if submit_btn and submit_btn.is_enabled():
#                     submit_btn.click()
#                     print("Application Submitted!")
#                     # page.wait_for_timeout(3000)
#                     # try:
#                     #     done_button = page.locator("button:has-text('Done')")
#                     #     done_button.wait_for(timeout=50000)
#                     #     done_button.click()
#                     #     print("Clicked 'Done'")
#                     # except Exception as e:
#                     #     print("Done button not found or error:", e)
#                     # break
#                     # Find the parent <button> that contains <span> with "Done" text
#                     try:
#                         done_button = page.locator('//button[.//span[normalize-space(text())="Done"]]')
#                         done_button.wait_for(state="visible", timeout=8000)
#                         done_button.scroll_into_view_if_needed()
#                         done_button.click()
#                         print("✅ Done button clicked.")
#                     except Exception as e:
#                         print("❌ Could not click Done button:", e)
#
#                         # Fallback: try closing the modal
#                         try:
#                             close_btn = page.locator('button[aria-label="Dismiss"]')
#                             close_btn.wait_for(state="visible", timeout=3000)
#                             close_btn.click()
#                             print("✅ Fallback: Closed modal.")
#                         except:
#                             print("❌ Neither Done nor Close button could be clicked.")
#
#
#                 elif review_btn and review_btn.is_enabled():
#                     review_btn.click()
#                     print("Reviewing Application...")
#                     page.wait_for_timeout(2000)
#                 elif next_btn and next_btn.is_enabled():
#                     next_btn.click()
#                     print("Moving to next step...")
#                     page.wait_for_timeout(2000)
#                 else:
#                     print("No further steps.")
#                     break
#             applied_jobs.append({
#                 "Job Title": title_text,
#                 "Company Name": company_text,
#                 "Location": location_text,
#                 "Job Description": desc_text,
#                 "form_labels": " | ".join(form_labels)  # New field
#             })
#
#             page.wait_for_timeout(3000)
#         except Exception as e:
#             print(f"Error in job #{idx + 1}: {e}")
#             continue
#     save_to_csv(applied_jobs)
#     print(f"Total jobs applied: {len(applied_jobs)}")
#
# def save_to_csv(data, filename="application_log.csv"):
#     file_exists = os.path.isfile(filename)
#     with open(filename, mode='a', newline='', encoding='utf-8') as file:
#         writer = csv.DictWriter(file, fieldnames=[
#             "Job Title", "Company Name", "Location", "Job Description", "form_labels"
#         ])
#         if not file_exists:
#             writer.writeheader()
#         for row in data:
#             writer.writerow(row)
#
#
#
# # def fill_all_fields_on_page(page):
# #     # pass
# #     resume_data = load_resume()
# #
# #     # Handle file uploads (resume)
# #     file_inputs = page.query_selector_all("input[type='file']")
# #     for file_input in file_inputs:
# #         try:
# #             file_input.set_input_files(RESUME_PATH)
# #             print(f"📎 Uploaded resume: {RESUME_PATH}")
# #         except Exception as e:
# #             print(f"❌ Resume upload failed: {e}")
# #
# #     # Inside your main form-filling logic:
# #     text_fields = page.query_selector_all("input:not([type=hidden]):not([readonly]), textarea")
# #     for field in text_fields:
# #         try:
# #             label = field.evaluate("""
# #                 el => {
# #                     const labelEl = el.closest('label')?.innerText ||
# #                                     el.parentElement?.querySelector('label')?.innerText ||
# #                                     el.getAttribute('aria-label') ||
# #                                     el.getAttribute('placeholder') ||
# #                                     '';
# #                     return labelEl.trim();
# #                 }
# #             """)
# #             if not label:
# #                 continue
# #
# #             answer = get_answer_from_llm(label, resume_data)
# #             if answer:
# #                 field.fill("")
# #                 field.fill(answer)
# #                 print(f"✍️ Filled: {label} => {answer}")
# #         except Exception as e:
# #             print(f"❌ Error filling field: {e}")
# #
# #     # Handle dropdowns
# #     selects = page.query_selector_all("select")
# #     for select in selects:
# #         try:
# #             label = select.evaluate("""
# #                 el => {
# #                     const labelEl = el.closest('label')?.innerText ||
# #                                     el.parentElement?.querySelector('label')?.innerText ||
# #                                     el.getAttribute('aria-label') ||
# #                                     '';
# #                     return labelEl.trim();
# #                 }
# #             """)
# #             if not label:
# #                 continue
# #
# #             answer = get_answer_from_llm(label, resume_data)
# #             if answer:
# #                 options = select.query_selector_all("option")
# #                 matched = False
# #                 for option in options:
# #                     option_text = option.inner_text().strip().lower()
# #                     if answer.strip().lower() in option_text or option_text in answer.strip().lower():
# #                         value = option.get_attribute("value")
# #                         select.select_option(value)
# #                         print(f"🔽 Selected: {label} => {option_text}")
# #                         matched = True
# #                         break
# #                 if not matched:
# #                     print(f"⚠️ No matching option found for {label} => {answer}")
# #         except Exception as e:
# #             print(f"❌ Dropdown fill error: {e}")
# #
# #     # Handle radio buttons
# #     radios = page.query_selector_all("input[type='radio']")
# #     radio_groups = {}
# #     for radio in radios:
# #         name = radio.get_attribute("name")
# #         if name not in radio_groups:
# #             radio_groups[name] = []
# #         radio_groups[name].append(radio)
# #
# #     for group_name, group_radios in radio_groups.items():
# #         try:
# #             label = group_radios[0].evaluate("""
# #                 el => {
# #                     const container = el.closest('fieldset') || el.closest('div');
# #                     return container?.innerText || '';
# #                 }
# #             """)
# #             if not label:
# #                 continue
# #
# #             answer = get_answer_from_llm(label, resume_data)
# #             for radio in group_radios:
# #                 value = radio.get_attribute("value") or radio.evaluate("el => el.labels?.[0]?.innerText || ''")
# #                 if value and (answer.strip().lower() in value.strip().lower() or value.strip().lower() in answer.strip().lower()):
# #                     radio.check()
# #                     print(f"🔘 Checked: {label} => {value}")
# #                     break
# #         except Exception as e:
# #             print(f"❌ Radio button error: {e}")
# #
#
# # def fill_all_fields_on_page(page):
#     # resume_data = load_resume()
#     #
#     # # ✅ Upload Resume
#     # file_inputs = page.query_selector_all("input[type='file']")
#     # for file_input in file_inputs:
#     #     try:
#     #         file_input.set_input_files(RESUME_PATH)
#     #         print(f"📎 Uploaded resume: {RESUME_PATH}")
#     #     except Exception as e:
#     #         print(f"❌ Resume upload failed: {e}")
#     #
#     # # ✅ Text Fields (input + textarea)
#     # text_fields = page.query_selector_all("input:not([type=hidden]):not([readonly]), textarea")
#     # for field in text_fields:
#     #     try:
#     #         label = field.evaluate("""
#     #             el => {
#     #                 const labelEl = el.closest('label')?.innerText ||
#     #                                 el.parentElement?.querySelector('label')?.innerText ||
#     #                                 el.getAttribute('aria-label') ||
#     #                                 el.getAttribute('placeholder') ||
#     #                                 '';
#     #                 return labelEl.trim();
#     #             }
#     #         """)
#     #         if not label:
#     #             continue
#     #
#     #         answer = get_answer_from_llm(label, resume_data)
#     #         if answer:
#     #             field.fill("")  # clear if needed
#     #             field.fill(answer)
#     #             print(f"✍️ Filled: {label} => {answer}")
#     #     except Exception as e:
#     #         print(f"❌ Error filling field: {e}")
#     #
#     # # ✅ Dropdowns
#     # selects = page.query_selector_all("select")
#     # for select in selects:
#     #     try:
#     #         label = select.evaluate("""
#     #             el => {
#     #                 const labelEl = el.closest('label')?.innerText ||
#     #                                 el.parentElement?.querySelector('label')?.innerText ||
#     #                                 el.getAttribute('aria-label') ||
#     #                                 '';
#     #                 return labelEl.trim();
#     #             }
#     #         """)
#     #         if not label:
#     #             continue
#     #
#     #         answer = get_answer_from_llm(label, resume_data)
#     #         if answer:
#     #             options = select.query_selector_all("option")
#     #             matched = False
#     #             for option in options:
#     #                 option_text = option.inner_text().strip().lower()
#     #                 if answer.strip().lower() in option_text or option_text in answer.strip().lower():
#     #                     value = option.get_attribute("value")
#     #                     select.select_option(value=value)
#     #                     print(f"🔽 Selected: {label} => {option_text}")
#     #                     matched = True
#     #                     break
#     #             if not matched:
#     #                 print(f"⚠️ No matching option found for {label} => {answer}")
#     #     except Exception as e:
#     #         print(f"❌ Dropdown fill error: {e}")
#     #
#     # # ✅ Radio Buttons
#     # radios = page.query_selector_all("input[type='radio']")
#     # radio_groups = {}
#     # for radio in radios:
#     #     name = radio.get_attribute("name")
#     #     if name not in radio_groups:
#     #         radio_groups[name] = []
#     #     radio_groups[name].append(radio)
#     #
#     # for group_name, group_radios in radio_groups.items():
#     #     try:
#     #         label = group_radios[0].evaluate("""
#     #             el => {
#     #                 const container = el.closest('fieldset') || el.closest('div');
#     #                 return container?.innerText || '';
#     #             }
#     #         """)
#     #         if not label:
#     #             continue
#     #
#     #         answer = get_answer_from_llm(label, resume_data)
#     #         for radio in group_radios:
#     #             value = radio.get_attribute("value")
#     #             label_text = radio.evaluate("el => el.labels?.[0]?.innerText || ''")
#     #             value_to_match = (value or label_text).strip().lower()
#     #
#     #             if answer.strip().lower() in value_to_match or value_to_match in answer.strip().lower():
#     #                 radio.check()
#     #                 print(f"🔘 Checked: {label} => {value_to_match}")
#     #                 break
#     #     except Exception as e:
#     #         print(f"❌ Radio button error: {e}")
#
#     print("🚀 Starting to fill application form...")
#
#     # ✅ Upload resume
# def fill_form_field(page, label_text, answer):
#         try:
#             # Match label and find next input
#             label = page.locator(f"text={label_text}").first
#             input_box = label.locator("xpath=following::input[1]")
#             if input_box.count() > 0:
#                 input_box.fill(answer)
#                 print(f"[✓] Filled: {label_text} → {answer}")
#             else:
#                 textarea = label.locator("xpath=following::textarea[1]")
#                 if textarea.count() > 0:
#                     textarea.fill(answer)
#                     print(f"[✓] Filled: {label_text} → {answer}")
#                 else:
#                     print(f"[!] No input/textarea found for: {label_text}")
#         except Exception as e:
#             print(f"[✗] Error filling '{label_text}': {e}")
#
#
#
# def main():
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         page = browser.new_page()
#         login_to_linkedin(page)
#         search_jobs(page)
#         filter_easy_apply_jobs(page)
#         fill_form_field(page, label_text, answer)
#
#         browser.close()
#
# if __name__ == "__main__":
#     main()



# #-------------------------Complete Scripts--------------------------------------------------------------------------------------
#
#
# import time
# import json
# import csv
# import os
# import requests
# from playwright.sync_api import sync_playwright
#
# #Load config.json
# with open("config.json", "r") as f:
#     config = json.load(f)
#
# with open("resume.txt", "r", encoding="utf-8") as file:
#     resume_text = file.read()
#
# LINKEDIN_USERNAME = config["LINKEDIN_USERNAME"]
# LINKEDIN_PASSWORD = config["LINKEDIN_PASSWORD"]
# RESUME_PATH = config["resume_path"]
# TARGET_JOB_TITLE = config["target_job_title"]
# TARGET_LOCATION = config["target_location"]
# LOG_FILE_PATH = config["log_file_path"]
# OPENWEBUI_API = config["OPENWEBUI_API_URL"]
# OPENWEBUI_MODEL = config["OPENWEBUI_MODEL"]
# MAX_JOBS_PER_RUN = config.get("max_jobs_per_run", 5)
# api_token = config["OPENWEBUI_API_KEY"]
#
# USER_NAME = "Manisha Walunj"  # Change as needed
# MODEL = "gemma"
#
#
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
#
# def log_application_data(job_title, company_name, location, description, form_labels):
#     log_file = 'application_log.csv'
#     file_exists = os.path.isfile(log_file)
#
#     with open(log_file, 'a', newline='', encoding='utf-8') as csvfile:
#         writer = csv.writer(csvfile)
#         if not file_exists:
#             writer.writerow([
#                 'Job Title',
#                 'Company Name',
#                 'Location',
#                 'Job Description',
#                 'form_labels'  # <-- Add this column
#             ])
#
#         writer.writerow([
#             job_title,
#             company_name,
#             location,
#             description,
#             form_labels,
#             ' | '.join(form_labels)  # <-- Join all label texts into a single string
#         ])
#
#
#
# def get_answer_from_llm(question, file_id):
#     chat_headers = {
#         "Authorization": f"Bearer {api_token}",
#         "Accept": "application/json",
#         "Content-Type": "application/json"
#     }
#
#
#     payload = {
#         "model": OPENWEBUI_MODEL,
#         "messages": [
#             {
#                 "role": "user",
#                 "content": (
#                 f"You are a helpful assistant. Answer the following job application question "
#                 f"based only on the resume content in the uploaded file.\n\n"
#                 f"If the question asks about years of experience with a specific skill or technology "
#                 f"(e.g., Angular, Node.js), extract that number from the resume if present. "
#                 f"Return a whole number between 0 and 30. If it's not mentioned, return 0.\n"
#                 f"If the question is about eligibility (Yes/No), answer only Yes or No.\n"
#                 f"If unsure, answer 0 for years or No for eligibility.\n\n"
#                 f"Resume:\n{resume_text}\n\n"
#                 f"Question: {question}"
# )
#             }
#         ],
#         "files": [{"type": "file", "id": file_id}]
#     }
#
#     response = requests.post(
#         f"{OPENWEBUI_API}/api/chat/completions",
#         headers=chat_headers,
#         json=payload
#     )
#
#     response.raise_for_status()
#     return response.json()['choices'][0]['message']['content']
#
# def login_to_linkedin(page):
#     page.goto("https://www.linkedin.com/login")
#     page.fill('input#username', LINKEDIN_USERNAME)
#     page.fill('input#password', LINKEDIN_PASSWORD)
#     page.click('button[type="submit"]')
#     try:
#         page.wait_for_url("https://www.linkedin.com/feed/", timeout=60000)
#         print("Logged in Successfully")
#     except:
#         page.screenshot(path="login_failed.png")
#         print("Login failed. Check credentials or captcha requirement.")
#         page.wait_for_timeout(10000)
#
# def search_jobs(page, job_title=TARGET_JOB_TITLE, job_location=TARGET_LOCATION):
#     page.goto("https://www.linkedin.com/jobs/")
#     if job_title:
#         try:
#             title_input = page.locator('//input[@aria-label="Search by title, skill, or company"]').first
#             title_input.wait_for(state="visible", timeout=20000)
#             title_input.click()
#             title_input.fill(job_title)
#             print("Entered Job Title")
#         except Exception as e:
#             print("Error entering job title:", e)
#     if job_location:
#         try:
#             location_input = page.locator('//input[@aria-label="City, state, or zip code"]').first
#             location_input.wait_for(state="visible", timeout=15000)
#             location_input.click()
#             location_input.press("Control+A")
#             location_input.press("Backspace")
#             location_input.fill(job_location)
#             page.wait_for_selector("ul[role='listbox'] li", timeout=5000)
#             page.keyboard.press("ArrowDown")
#             page.keyboard.press("Enter")
#             page.wait_for_timeout(5000)
#             print("Entered Job Location")
#         except Exception as e:
#             print("Error entering job location:", e)
#
# def select_custom_dropdown(field, answer):
#     try:
#         # Click the field to open dropdown
#         field.click()
#         time.sleep(0.5)  # Wait for dropdown to render
#
#         # Locate the open dropdown container
#         dropdown_panel = field.page.locator("div[role='listbox'], ul[role='listbox'], div[aria-expanded='true']")
#
#         # Try to match answer exactly or partially
#         option = dropdown_panel.get_by_text(answer, exact=True)
#         if not option.is_visible():
#             option = dropdown_panel.get_by_text(answer)
#
#         option.click()
#         print(f"✅ Custom dropdown option selected: {answer}")
#     except Exception as e:
#         print(f"❌ Failed to select from custom dropdown: {e}")
#
#
# def extract_and_fill_form_fields_across_steps(page, file_id):
#     print("\n📋 Extracting and filling form fields from all steps:")
#     seen = set()
#
#     def fill_field(field, label_text):
#         try:
#             tag = field.evaluate("el => el.tagName.toLowerCase()")
#             input_type = field.get_attribute("type") or ""
#
#
#
#             # ✅ Skip early if field is already filled or checked
#             if tag == "input":
#                 if input_type in ["checkbox", "radio"]:
#                     if field.is_checked():
#                         print(f"⏭️ Skipping already selected checkbox/radio: {label_text}")
#                         return
#                 else:
#                     current_value = field.input_value().strip()
#                     if current_value:
#                         print(f"⏭️ Skipping already filled input: {label_text}")
#                         return
#
#             elif tag == "select":
#                 current_value = field.input_value().strip()
#                 if current_value:
#                     print(f"⏭️ Skipping already selected dropdown: {label_text}")
#                     return
#
#             elif tag == "textarea":
#                 current_value = field.input_value().strip()
#                 if current_value:
#                     print(f"⏭️ Skipping already filled textarea: {label_text}")
#                     return
#
#             # ⏳ Only call LLM if filling is actually needed
#             answer = get_answer_from_llm(label_text, file_id)
#             print(f"Q: {label_text}")
#             print(f"A: {answer}")
#
#             if tag == "input":
#                 if input_type in ["checkbox", "radio"]:
#                     try:
#                         parent = field.locator("xpath=ancestor::fieldset[1] | ancestor::div[1]")
#                         matched = False
#                         options = parent.locator("label, div").all()
#                         print(f"🔍 Trying to match answer '{answer}' for question: {label_text}")
#                         for option in options:
#                             try:
#                                 label = option.inner_text().strip().lower()
#                                 if label and answer.lower() in label:
#                                     option.click()
#                                     print(f"✅ Clicked radio/checkbox option: '{label}'")
#                                     matched = True
#                                     break
#                             except Exception as e:
#                                 print(f"⚠️ Error clicking option '{label}': {e}")
#                         if not matched:
#                             print(f"❌ No matching radio/checkbox found for: '{answer}'")
#                     except Exception as e:
#                         print(f"❌ Error finding fieldset for radio/checkbox: {e}")
#                 else:
#                     try:
#                         field.fill(answer)
#                         print(f"📝 Filled input with: {answer}")
#                     except Exception as e:
#                         print(f"❌ Failed to fill input: {e}")
#
#             elif tag == "select":
#                 try:
#                     field.select_option(label=answer)
#                     print(f"✅ Selected dropdown option: {answer}")
#                 except Exception as e:
#                     print(f"❌ Failed to select dropdown option '{answer}': {e}")
#
#             elif tag == "textarea":
#                 try:
#                     field.fill(answer)
#                     print(f"📝 Filled textarea with: {answer}")
#                 except Exception as e:
#                     print(f"❌ Failed to fill textarea: {e}")
#
#             else:
#                 print(f"⚠️ Unsupported field tag: {tag}")
#         except Exception as e:
#             print(f"❌ Error filling field for label '{label_text}': {e}")
#
#     #fields allready fill then also check
#     # def fill_field(field, label_text):
#     #     try:
#     #         answer = get_answer_from_llm(label_text, file_id)
#     #         print(f"Q: {label_text}")
#     #         print(f"A: {answer}")
#     #
#     #         tag = field.evaluate("el => el.tagName.toLowerCase()")
#     #         input_type = field.get_attribute("type") or ""
#     #
#     #         if tag == "input":
#     #             if input_type in ["checkbox", "radio"]:
#     #                 # Skip if already checked
#     #                 if field.is_checked():
#     #                     print(f"⏭️ Skipping already selected checkbox/radio: {label_text}")
#     #                     return
#     #                 # Proceed to match and click
#     #                 try:
#     #                     parent = field.locator("xpath=ancestor::fieldset[1] | ancestor::div[1]")
#     #                     matched = False
#     #                     options = parent.locator("label, div").all()
#     #                     print(f"🔍 Trying to match answer '{answer}' for question: {label_text}")
#     #                     for option in options:
#     #                         try:
#     #                             label = option.inner_text().strip().lower()
#     #                             if label and answer.lower() in label:
#     #                                 option.click()
#     #                                 print(f"✅ Clicked radio/checkbox option: '{label}'")
#     #                                 matched = True
#     #                                 break
#     #                         except Exception as e:
#     #                             print(f"⚠️ Error clicking option '{label}': {e}")
#     #                     if not matched:
#     #                         print(f"❌ No matching radio/checkbox found for: '{answer}'")
#     #                 except Exception as e:
#     #                     print(f"❌ Error finding fieldset for radio/checkbox: {e}")
#     #             else:
#     #                 current_value = field.input_value().strip()
#     #                 if current_value:
#     #                     print(f"⏭️ Skipping already filled input: {label_text}")
#     #                     return
#     #                 try:
#     #                     field.fill(answer)
#     #                     print(f"📝 Filled input with: {answer}")
#     #                 except Exception as e:
#     #                     print(f"❌ Failed to fill input: {e}")
#     #
#     #         elif tag == "select":
#     #             selected = field.input_value().strip()
#     #             if selected:
#     #                 print(f"⏭️ Skipping already selected dropdown: {label_text}")
#     #                 return
#     #             try:
#     #                 field.select_option(label=answer)
#     #                 print(f"✅ Selected dropdown option: {answer}")
#     #             except Exception as e:
#     #                 print(f"❌ Failed to select dropdown option '{answer}': {e}")
#     #
#     #         elif tag == "textarea":
#     #             current_value = field.input_value().strip()
#     #             if current_value:
#     #                 print(f"⏭️ Skipping already filled textarea: {label_text}")
#     #                 return
#     #             field.fill(answer)
#     #             print(f"📝 Filled textarea with: {answer}")
#     #
#     #         else:
#     #             print(f"⚠️ Unsupported field tag: {tag}")
#     #     except Exception as e:
#     #         print(f"❌ Error filling field for label '{label_text}': {e}")
#
#
#     # def fill_field(field, label_text):
#     #     try:
#     #         answer = get_answer_from_llm(label_text, file_id)
#     #         print(f"Q: {label_text}")
#     #         print(f"A: {answer}")
#     #
#     #         tag = field.evaluate("el => el.tagName.toLowerCase()")
#     #         input_type = field.get_attribute("type") or ""
#     #
#     #         if tag == "input":
#     #             if input_type in ["checkbox", "radio"]:
#     #                 try:
#     #                     # Locate parent block
#     #                     parent = field.locator("xpath=ancestor::fieldset[1] | ancestor::div[1]")
#     #                     matched = False
#     #
#     #                     # Get all clickable options within the container
#     #                     options = parent.locator("label, div").all()
#     #
#     #                     print(f"🔍 Trying to match answer '{answer}' for question: {label_text}")
#     #
#     #                     for option in options:
#     #                         try:
#     #                             label = option.inner_text().strip().lower()
#     #                             if label and answer.lower() in label:
#     #                                 option.click()
#     #                                 print(f"✅ Clicked radio/checkbox option: '{label}'")
#     #                                 matched = True
#     #                                 break
#     #                         except Exception as e:
#     #                             print(f"⚠️ Error clicking option '{label}': {e}")
#     #
#     #                     if not matched:
#     #                         print(f"❌ No matching radio/checkbox found for: '{answer}'")
#     #                 except Exception as e:
#     #                     print(f"❌ Error finding fieldset for radio/checkbox: {e}")
#     #
#     #             else:
#     #                 try:
#     #                     field.fill(answer)
#     #                     print(f"📝 Filled input with: {answer}")
#     #                 except Exception as e:
#     #                     print(f"❌ Failed to fill input: {e}")
#     #
#     #         elif tag == "select":
#     #             try:
#     #                 # Select by visible text match
#     #                 field.select_option(label=answer)
#     #                 print(f"✅ Selected dropdown option: {answer}")
#     #             except Exception as e:
#     #                 print(f"❌ Failed to select dropdown option '{answer}': {e}")
#     #
#     #         elif tag == "select":
#     #
#     #             try:
#     #
#     #                 field.select_option(label=answer)
#     #
#     #                 print(f"✅ Native select worked for: {answer}")
#     #
#     #             except:
#     #
#     #                 print(f"⚠️ Native select failed for '{label_text}', trying custom dropdown fallback.")
#     #
#     #                 select_custom_dropdown(field, answer)
#     #
#     #         elif tag == "textarea":
#     #             field.fill(answer)
#     #         else:
#     #             print(f"⚠️ Unsupported field tag: {tag}")
#     #     except Exception as e:
#     #         print(f"❌ Error filling field for label '{label_text}': {e}")
#     #
#
#
#     def process_fields_in_modal():
#         try:
#             modal = page.query_selector("div.jobs-easy-apply-modal")
#             if not modal:
#                 print("❌ Easy Apply modal not found.")
#                 return False
#
#             # Label-associated fields
#             labels = modal.query_selector_all("label")
#             for label in labels:
#                 label_text = label.inner_text().strip()
#                 if not label_text or label_text in seen:
#                     continue
#                 seen.add(label_text)
#
#                 # Try 'for' attribute
#                 for_attr = label.get_attribute("for")
#                 field = None
#                 if for_attr:
#                     field = modal.query_selector(f"#{for_attr}")
#                 if not field:
#                     field = label.query_selector("input, select, textarea") or label.evaluate_handle("el => el.nextElementSibling")
#
#                 if field:
#                     print(f"🔹 Label: {label_text}")
#                     fill_field(field, label_text)
#
#             # Fields with aria-label or placeholder
#             other_fields = modal.query_selector_all("input, select, textarea")
#             for field in other_fields:
#                 if not field.is_enabled():
#                     continue
#                 attr = field.get_attribute("aria-label") or field.get_attribute("placeholder")
#                 if attr and attr.strip() not in seen:
#                     seen.add(attr.strip())
#                     print(f"🔸 Field: {attr.strip()}")
#                     fill_field(field, attr.strip())
#
#             return True
#         except Exception as e:
#             print(f"❌ Error in modal field processing: {e}")
#             return False
#
#     process_fields_in_modal()
#
#     while True:
#         try:
#             next_button = page.locator(
#                 "button:has-text('Next'), button:has-text('Review'), button:has-text('Submit')"
#             ).first
#
#             if next_button.is_enabled():
#                 btn_text = next_button.inner_text().strip()
#                 print(f"\n➡️ Clicking: {btn_text}")
#                 next_button.click()
#                 page.wait_for_timeout(1500)
#
#                 try:
#                     # Try common variants of the Done button
#                     done_span = page.locator(
#                         "span:has-text('Done'), span:has-text('Close'), span:has-text('Back to search')").first
#                     done_span.wait_for(state="visible", timeout=5000)
#                     done_button = done_span.locator("xpath=ancestor::button[1]")
#
#                     if done_button.is_visible() and done_button.is_enabled():
#                         done_button.click()
#                         print("🎉 Clicked 'Done' button successfully.")
#                     else:
#                         print("⚠️ Done button found but not clickable. Forcing with JS.")
#                         page.evaluate("btn => btn.click()", done_button)
#
#                     page.wait_for_timeout(1500)
#                 except Exception as e:
#                     print(f"❌ Failed to click Done button: {e}")
#
#                 process_fields_in_modal()
#
#                 if btn_text == "Submit":
#                     print("✅ Reached final step.")
#                     break
#
#             else:
#                 print("❌ No enabled next/review/submit button.")
#                 break
#         except Exception as e:
#             print(f"❌ Navigation failed: {e}")
#             break
#
#
#
#
# def filter_easy_apply_jobs(page,file_id):
#     # form_labels = extract_all_form_labels_across_steps(page)
#     applied_jobs = []
#     try:
#         filter_btn = page.locator("button:has-text('Easy Apply')").first
#         filter_btn.click()
#
#         print("Filtered to Easy Apply jobs")
#         page.wait_for_timeout(3000)
#     except Exception as e:
#         print("Easy Apply filter error:", e)
#     page.wait_for_selector("div.job-card-container", timeout=10000)
#     jobs = page.query_selector_all("div.job-card-container")
#     for idx, job in enumerate(jobs):
#         if idx >= MAX_JOBS_PER_RUN:
#             break
#         try:
#             job.click()
#             page.wait_for_timeout(3000)
#             apply_btn = page.query_selector("button.jobs-apply-button")
#             if not apply_btn:
#                 print("Skipping non-Easy Apply job")
#                 continue
#             job_title = page.query_selector("h2.topcard__title") or page.query_selector("h1")
#
#             company_name = (
#                     page.query_selector("a.topcard__org-name-link") or
#                     page.query_selector("span.topcard__flavor") or
#                     page.query_selector("div.artdeco-entity-lockup__subtitle")
#             )
#             location = (
#                     page.query_selector("span.jobs-unified-top-card__bullet") or
#                     page.query_selector("span.topcard__flavor--bullet") or
#                     page.query_selector("div.artdeco-entity-lockup__caption")
#             )
#             job.click()
#             page.wait_for_timeout(5000)
#
#             right_panel = page.query_selector("div.jobs-details") or page.query_selector("div.jobs-search__job-details")
#             if right_panel:
#                 right_panel.scroll_into_view_if_needed()
#                 page.mouse.wheel(0, 5000)
#                 page.wait_for_timeout(2000)
#
#             # job_description = page.query_selector("div.description__text")
#             job_description = (
#                 page.query_selector("div.job-details-module.jobs-description")
#             )
#
#             title_text = job_title.inner_text().strip() if job_title else "N/A"
#             company_text = company_name.inner_text().strip() if company_name else "N/A"
#             location_text = location.inner_text().strip() if location else "N/A"
#             desc_text = job_description.inner_text().strip() if job_description else "N/A"
#             apply_btn.click()
#             page.wait_for_timeout(2000)
#
#             # fill_easy_apply_form_with_llm(page, file_id)
#             form_labels = extract_and_fill_form_fields_across_steps(page, file_id)
#             fill_easy_apply_form_with_llm(page, file_id, form_labels)
#
#             log_application_data(job_title, company_name, location, desc_text, form_labels)
#
#
#             while True:
#                 page.wait_for_timeout(1000)
#                 # fill_all_fields_on_page(page)
#                 next_btn = page.query_selector("button:has-text('Next')")
#                 review_btn = page.query_selector("button:has-text('Review')")
#                 submit_btn = page.query_selector("button:has-text('Submit')")
#                 if submit_btn and submit_btn.is_enabled():
#                     submit_btn.click()
#                     print("Application Submitted!")
#                     page.wait_for_timeout(3000)  # Wait for Done modal to render
#                     try:
#                         # Try common variants of the Done button
#                         done_span = page.locator(
#                             "span:has-text('Done'), span:has-text('Close'), span:has-text('Back to search')").first
#                         done_span.wait_for(state="visible", timeout=5000)
#                         done_button = done_span.locator("xpath=ancestor::button[1]")
#
#                         if done_button.is_visible() and done_button.is_enabled():
#                             done_button.click()
#                             print("🎉 Clicked 'Done' button successfully.")
#                         else:
#                             print("⚠️ Done button found but not clickable. Forcing with JS.")
#                             page.evaluate("btn => btn.click()", done_button)
#
#                         page.wait_for_timeout(1500)
#                     except Exception as e:
#                         print(f"❌ Failed to click Done button: {e}")
#
#                 elif review_btn and review_btn.is_enabled():
#                     review_btn.click()
#                     print("Reviewing Application...")
#                     page.wait_for_timeout(2000)
#                 elif next_btn and next_btn.is_enabled():
#                     next_btn.click()
#                     print("Moving to next step...")
#                     page.wait_for_timeout(2000)
#                 else:
#                     print("No further steps.")
#                     break
#             applied_jobs.append({
#                 "Job Title": title_text,
#                 "Company Name": company_text,
#                 "Location": location_text,
#                 "Job Description": desc_text,
#                 "form_labels": " | ".join(form_labels)  # New field
#             })
#
#             page.wait_for_timeout(3000)
#         except Exception as e:
#             print(f"Error in job #{idx + 1}: {e}")
#             continue
#     save_to_csv(applied_jobs)
#     print(f"Total jobs applied: {len(applied_jobs)}")
#
# def save_to_csv(data, filename="application_log.csv"):
#     file_exists = os.path.isfile(filename)
#     with open(filename, mode='a', newline='', encoding='utf-8') as file:
#         writer = csv.DictWriter(file, fieldnames=[
#             "Job Title", "Company Name", "Location", "Job Description", "form_labels"
#         ])
#         if not file_exists:
#             writer.writeheader()
#         for row in data:
#             writer.writerow(row)
# def normalize_answer(text):
#     text = text.strip().lower()
#     if text in ["yes", "y", "yeah", "1"]:
#         return "Yes"
#     elif text in ["no", "n", "nope", "0"]:
#         return "No"
#     return text.capitalize()  # Capitalize other text like "3 years"
#
# def fill_easy_apply_form_with_llm(page, file_id):
#     try:
#         modal = page.wait_for_selector("div.jobs-easy-apply-modal", timeout=7000)
#     except Exception:
#         print(" ..Easy Apply modal did not appear.")
#         return
#
#
#     # Get all labels inside the modal
#     labels = modal.query_selector_all("label, span, p")  # broaden span/p if labels are inside those
#
#     for label in labels:
#         label_text = label.inner_text().strip()
#         if not label_text:
#             continue
#
#         print(f"Question: {label_text}")
#
#         # Ask LLM for answer based on the label text question
#         answer = get_answer_from_llm(label_text, file_id).strip()
#         print(f"Answer from LLM: {answer}")
#
#         # Find related input element:
#         input_id = label.get_attribute("for")
#         input_elem = None
#         if input_id:
#             input_elem = page.query_selector(f"#{input_id}")
#         else:
#             # fallback: try to find input/select/textarea near label
#             input_elem = label.query_selector("input, select, textarea")
#
#         if not input_elem:
#             print(f"  Could not find input element for question: {label_text}")
#             continue
#
#         tag_name = input_elem.evaluate("el => el.tagName.toLowerCase()")
#         input_type = input_elem.get_attribute("type") or ""
#
#         try:
#             if tag_name == "input":
#                 if input_type in ["text", "number"]:
#                     input_elem.fill(answer)
#                 elif input_type == "radio":
#                     # Find radio buttons with same name and pick matching value
#                     name = input_elem.get_attribute("name")
#                     radios = page.query_selector_all(f"input[type=radio][name='{name}']")
#                     for r in radios:
#                         val = r.get_attribute("value")
#                         if val and answer.lower() in val.lower():
#                             r.check()
#                             break
#                 elif input_type == "checkbox":
#                     if answer.lower() in ["yes", "true", "1"]:
#                         input_elem.check()
#                     else:
#                         input_elem.uncheck()
#             elif tag_name == "select":
#                 # Select option matching the answer
#                 options = input_elem.query_selector_all("option")
#                 for opt in options:
#                     opt_text = opt.inner_text().strip().lower()
#                     if answer.lower() in opt_text:
#                         input_elem.select_option(opt.get_attribute("value"))
#                         break
#             elif tag_name == "select":
#                 # Get all options and match answer
#                 options = input_elem.query_selector_all("option")
#                 matched = False
#                 for opt in options:
#                     opt_text = opt.inner_text().strip().lower()
#                     if answer.lower() in opt_text or opt_text in answer.lower():
#                         input_elem.select_option(opt.get_attribute("value"))
#                         matched = True
#                         break
#                 if not matched:
#                     print(f"  ⚠️ No matching option for '{answer}' in select dropdown: {label_text}")
#
#             elif tag_name == "textarea":
#                 input_elem.fill(answer)
#             else:
#                 print(f"  Unsupported input type: {tag_name} / {input_type}")
#         except Exception as e:
#             print(f"  Error filling input for question '{label_text}': {e}")
#
#
# def main():
#
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         page = browser.new_page()
#         login_to_linkedin(page)
#         search_jobs(page)
#         file_id = upload_resume_get_file_id(RESUME_PATH)  # <- Get file ID here
#         filter_easy_apply_jobs(page, file_id)
#
#         browser.close()
#
# if __name__ == "__main__":
#     main()
#
#
#
#
#
#
#


# applying mutliple jobs issue only cv and dropdown

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

def select_custom_dropdown(field, answer):
    try:
        # Click the field to open dropdown
        field.click()
        time.sleep(0.5)  # Wait for dropdown to render

        # Locate the open dropdown container
        dropdown_panel = field.page.locator("div[role='listbox'], ul[role='listbox'], div[aria-expanded='true']")

        # Try to match answer exactly or partially
        option = dropdown_panel.get_by_text(answer, exact=True)
        if not option.is_visible():
            option = dropdown_panel.get_by_text(answer)

        option.click()
        print(f"✅ Custom dropdown option selected: {answer}")
    except Exception as e:
        print(f"❌ Failed to select from custom dropdown: {e}")


def extract_and_fill_form_fields_across_steps(page, file_id):
    print("\n📋 Extracting and filling form fields from all steps:")
    seen = set()

    def fill_field(field, label_text):
        try:
            tag = field.evaluate("el => el.tagName.toLowerCase()")
            input_type = field.get_attribute("type") or ""

            # ✅ Skip early if field is already filled or checked
            if tag == "input":
                if input_type in ["checkbox", "radio"]:
                    if field.is_checked():
                        print(f"⏭️ Skipping already selected checkbox/radio: {label_text}")
                        return
                else:
                    current_value = field.input_value().strip()
                    if current_value:
                        print(f"⏭️ Skipping already filled input: {label_text}")
                        return

            elif tag == "select":
                current_value = field.input_value().strip()
                if current_value:
                    print(f"⏭️ Skipping already selected dropdown: {label_text}")
                    return

            elif tag == "textarea":
                current_value = field.input_value().strip()
                if current_value:
                    print(f"⏭️ Skipping already filled textarea: {label_text}")
                    return

            # ⏳ Only call LLM if filling is actually needed
            answer = get_answer_from_llm(label_text, file_id)
            print(f"Q: {label_text}")
            print(f"A: {answer}")

            if tag == "input":
                if input_type in ["checkbox", "radio"]:
                    try:
                        parent = field.locator("xpath=ancestor::fieldset[1] | ancestor::div[1]")
                        matched = False
                        options = parent.locator("label, div").all()
                        print(f"🔍 Trying to match answer '{answer}' for question: {label_text}")
                        for option in options:
                            try:
                                label = option.inner_text().strip().lower()
                                if label and answer.lower() in label:
                                    option.click()
                                    print(f"✅ Clicked radio/checkbox option: '{label}'")
                                    matched = True
                                    break
                            except Exception as e:
                                print(f"⚠️ Error clicking option '{label}': {e}")
                        if not matched:
                            print(f"❌ No matching radio/checkbox found for: '{answer}'")
                    except Exception as e:
                        print(f"❌ Error finding fieldset for radio/checkbox: {e}")
                else:
                    try:
                        field.fill(answer)
                        print(f"📝 Filled input with: {answer}")
                    except Exception as e:
                        print(f"❌ Failed to fill input: {e}")

            elif tag == "select":
                try:
                    field.select_option(label=answer)
                    print(f"✅ Selected dropdown option: {answer}")
                except Exception as e:
                    print(f"❌ Failed to select dropdown option '{answer}': {e}")

            elif tag == "textarea":
                try:
                    field.fill(answer)
                    print(f"📝 Filled textarea with: {answer}")
                except Exception as e:
                    print(f"❌ Failed to fill textarea: {e}")

            else:
                print(f"⚠️ Unsupported field tag: {tag}")
        except Exception as e:
            print(f"❌ Error filling field for label '{label_text}': {e}")

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
                return

            process_fields_in_modal()

        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return

    # while True:
    #     try:
    #         next_button = page.locator(
    #             "button:has-text('Next'), button:has-text('Review'), button:has-text('Submit')"
    #         ).first
    #
    #         if next_button.is_enabled():
    #             btn_text = next_button.inner_text().strip()
    #             print(f"\n➡️ Clicking: {btn_text}")
    #             next_button.click()
    #             page.wait_for_timeout(1500)
    #
    #             try:
    #                 # Try common variants of the Done button
    #                 done_span = page.locator(
    #                     "span:has-text('Done'), span:has-text('Close'), span:has-text('Back to search')").first
    #                 done_span.wait_for(state="visible", timeout=5000)
    #                 done_button = done_span.locator("xpath=ancestor::button[1]")
    #
    #                 if done_button.is_visible() and done_button.is_enabled():
    #                     done_button.click()
    #                     print("🎉 Clicked 'Done' button successfully.")
    #                 else:
    #                     print("⚠️ Done button found but not clickable. Forcing with JS.")
    #                     page.evaluate("btn => btn.click()", done_button)
    #                     break
    #
    #                 page.wait_for_timeout(1500)
    #             except Exception as e:
    #                 print(f"❌ Failed to click Done button: {e}")
    #
    #             # process_fields_in_modal()
    #
    #             if btn_text == "Submit":
    #                 print("✅ Reached final step.")
    #                 break
    #
    #         else:
    #             print("❌ No enabled next/review/submit button.")
    #             break
    #     except Exception as e:
    #         print(f"❌ Navigation failed: {e}")
    #         break

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

            # form_labels = extract_and_fill_form_fields_across_steps(page, file_id)
            extract_and_fill_form_fields_across_steps(page, file_id)

            fill_easy_apply_form_with_llm(page, file_id)

            log_application_data(title_text, company_text, location_text, desc_text)
            applied_jobs.append({
                "Job Title": title_text,
                "Company Name": company_text,
                "Location": location_text,
                "Job Description": desc_text,
            })
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



                # if submit_btn and submit_btn.is_enabled():
                #     submit_btn.click()
                #     print("✅ Submitted application.")
                #
                #     # Wait for modal to settle after submit
                #     page.wait_for_timeout(4000)


                    # try:
                    #     # Wait for a Done-like button to appear
                    #     done_button = page.wait_for_selector(
                    #         "button:has-text('Done'), button:has-text('Close'), button:has-text('Back to search')",
                    #         timeout=10000
                    #     )
                    #     done_button.click()
                    #     print("✅ Clicked Done/Close button.")
                    #
                    #     # Wait for modal to close before continuing
                    #     page.wait_for_selector("div.jobs-easy-apply-modal", state="detached", timeout=8000)
                    #     print("✅ Modal closed, ready to move to next job.")
                    # except Exception as e:
                    #     print(f"❌ Failed to click Done button or close modal: {e}")
                    #     page.screenshot(path="done_button_error.png")
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

    # print(f"Total jobs applied: {len(applied_jobs)}")


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
def normalize_answer(text):
    text = text.strip().lower()
    if text in ["yes", "y", "yeah", "1"]:
        return "Yes"
    elif text in ["no", "n", "nope", "0"]:
        return "No"
    return text.capitalize()  # Capitalize other text like "3 years"

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








