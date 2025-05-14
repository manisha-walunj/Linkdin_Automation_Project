# import json
# from playwright.sync_api import sync_playwright  # Use sync_playwright
# import csv
# import os
#
#
# # Load config.json
# with open("config.json", "r") as f:
#     config = json.load(f)
#
# LINKEDIN_USERNAME = config["LINKEDIN_USERNAME"]
# LINKEDIN_PASSWORD = config["LINKEDIN_PASSWORD"]
# RESUME_PATH = config["resume_path"]
# TARGET_JOB_TITLE = config["target_job_title"]
# TARGET_LOCATION = config["target_location"]
# LOG_FILE_PATH = config["log_file_path"]
# MAX_JOBS_PER_RUN = config.get("max_jobs_per_run", 5)
# def login_to_linkedin(page):
#     # Go to LinkedIn login page
#     page.goto("https://www.linkedin.com/login")
#
#     # Fill in credentials
#     page.fill('input#username', LINKEDIN_USERNAME)
#     page.fill('input#password', LINKEDIN_PASSWORD)
#
#     # Click login
#     page.click('button[type="submit"]')
#
#     try:
#         page.wait_for_url("https://www.linkedin.com/feed/", timeout=30000)
#         print("Logged in Successfully")
#     except:
#         page.screenshot(path="login_failed.png")
#         print("Login failed. Check credentials or captcha requirement.")
#         page.wait_for_timeout(10000)  # Pause 10 seconds before closing
#
# def search_jobs(page,job_title=TARGET_JOB_TITLE,job_location=TARGET_LOCATION):
#     # Go to the LinkedIn Jobs section
#     page.goto("https://www.linkedin.com/jobs/")
#     if job_title:
#         try:
#             title_input = page.locator('//input[@aria-label="Search by title, skill, or company"]').first
#             title_input.wait_for(state="visible", timeout=20000)
#             title_input.click()
#             title_input.fill(job_title)
#             print("Enter Job Title")
#         except Exception as e:
#             print("Error entering job title:", e)
#
#     if job_location:
#         try:
#             location_input = page.locator('//input[@aria-label="City, state, or zip code"]').first
#             location_input.wait_for(state="visible", timeout=15000)
#             location_input.click()
#             location_input.press("Control+A")
#             location_input.press("Backspace")
#             location_input.fill(job_location)
#
#             # Wait for LinkedIn's autocomplete dropdown to appear
#             page.wait_for_selector("ul[role='listbox'] li", timeout=5000)
#
#             # Now press ArrowDown + Enter to select the first suggestion
#             page.keyboard.press("ArrowDown")
#             page.keyboard.press("Enter")
#
#             page.wait_for_timeout(5000)  # Let the page settle
#             print("Filled Job Location")
#         except Exception as e:
#             print("Error entering job location:", e)
#
#
# def filter_easy_apply_jobs(page):
#     applied_jobs = []
#
#     try:
#         filter_btn = page.locator("button:has-text('Easy Apply')").first
#         filter_btn.click()
#         print("Filtered to Easy Apply jobs")
#         page.wait_for_timeout(3000)
#     except Exception as e:
#         print("Easy Apply filter error:", e)
#
#     page.wait_for_selector("div.job-card-container", timeout=10000)
#     jobs = page.query_selector_all("div.job-card-container")
#
#     for idx, job in enumerate(jobs):
#         try:
#             job.click()
#             page.wait_for_timeout(3000)
#
#             apply_btn = page.query_selector("button.jobs-apply-button")
#             if not apply_btn:
#                 print("Skipping non-Easy Apply job")
#                 continue
#
#             # Extract job info BEFORE clicking apply
#             job_title = page.query_selector("h2.topcard__title") or page.query_selector("h1")
#             # # company_name = page.query_selector("span.topcard__flavor")
#             # company_name = page.query_selector("a.topcard__org-name-link") or page.query_selector("span.topcard__flavor")
#             # # location = page.query_selector("span.topcard__flavor--bullet")
#             # location = page.query_selector("span.jobs-unified-top-card__bullet") or page.query_selector("span.topcard__flavor--bullet")
#             # ✅ Company Name
#             company_name = (
#                     page.query_selector("a.topcard__org-name-link") or
#                     page.query_selector("span.topcard__flavor") or
#                     page.query_selector("div.artdeco-entity-lockup__subtitle")
#             )
#
#             # ✅ Location
#             location = (
#                     page.query_selector("span.jobs-unified-top-card__bullet") or
#                     page.query_selector("span.topcard__flavor--bullet") or
#                     page.query_selector("div.artdeco-entity-lockup__caption")
#             )
#             job.click()
#             page.wait_for_timeout(5000)
#             right_panel = page.query_selector("div.jobs-details") or page.query_selector("div.jobs-search__job-details")
#             if right_panel:
#                 right_panel.scroll_into_view_if_needed()
#                 page.mouse.wheel(0, 5000)
#                 page.wait_for_timeout(2000)
#
#             # job_description = page.query_selector("div.description__text")
#             job_description = (
#                     # page.query_selector("div.show-more-less-html__markup")
#                     # page.query_selector("div.description__text")
#                     # page.query_selector("article.jobs-description__container")
#                     # page.query_selector("div.jobs-description--reformatted") or
#                     page.query_selector("div.job-details-module.jobs-description")
#             )
#
#             title_text = job_title.inner_text().strip() if job_title else "N/A"
#             company_text = company_name.inner_text().strip() if company_name else "N/A"
#             location_text = location.inner_text().strip() if location else "N/A"
#             desc_text = job_description.inner_text().strip() if job_description else "N/A"
#
#             apply_btn.click()
#             page.wait_for_timeout(2000)
#
#             while True:
#                 page.wait_for_timeout(1000)
#
#                 fill_all_fields_on_page(page)  # your form filler
#
#                 next_btn = page.query_selector("button:has-text('Next')")
#                 review_btn = page.query_selector("button:has-text('Review')")
#                 submit_btn = page.query_selector("button:has-text('Submit')")
#
#                 if submit_btn and submit_btn.is_enabled():
#                     submit_btn.click()
#                     print("Application Submitted!")
#                     page.wait_for_timeout(3000)
#                     try:
#                         # Wait for the Done button to appear
#                         done_button = page.locator("button:has-text('Done')")
#                         done_button.wait_for(timeout=5000)  # wait up to 5 seconds
#                         done_button.click()
#                         print("Application submitted and 'Done' button clicked.")
#                     except Exception as e:
#                         print("Done button not found or not clickable:", e)
#
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
#
#             print(f"Applied to job #{idx + 1}: {page.url}")
#
#             applied_jobs.append({
#                 "Job Title": title_text,
#                 "Company Name": company_text,
#                 "Location": location_text,
#                 "Job Description": desc_text,
#             })
#
#             page.wait_for_timeout(3000)
#
#         except Exception as e:
#             print(f"Error in job #{idx + 1}: {e}")
#             continue
#
#     # Save to CSV
#     save_to_csv(applied_jobs)
#     print(f"Total jobs applied: {len(applied_jobs)}")
#
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
#
# def fill_all_fields_on_page(page):# use llm to fill data
#     pass
#     # file_inputs = page.query_selector_all("input[type='file']") #Upload Resume
#     # for file_input in file_inputs:
#     #     try:
#     #         file_input.set_input_files(RESUME_PATH)
#     #         print(f"📎 Uploaded resume from {RESUME_PATH}")
#     #     except Exception as e:
#     #         print(f"Resume upload failed: {e}")
#     # text_fields = page.query_selector_all("input:not([type=hidden]):not([readonly]), textarea")
#     # for field in text_fields:
#     #     try:
#     #         label = field.evaluate("el => el.closest('label')?.innerText || el.closest('div')?.innerText || ''")
#     #         value = get_resume_value(label)
#     #         if value:
#     #             field.fill(str(value))
#     #     except:
#     #         pass
#     #
#     # # === Standard dropdowns <select> ===
#     # dropdowns = page.query_selector_all("select")
#     # for dropdown in dropdowns:
#     #     try:
#     #         label = dropdown.evaluate("el => el.closest('label')?.innerText || el.closest('div')?.innerText || ''")
#     #         value = get_resume_value(label)
#     #         if value:
#     #             options = dropdown.query_selector_all("option")
#     #             for option in options:
#     #                 option_text = option.inner_text().strip().lower()
#     #                 if value.lower() in option_text:
#     #                     dropdown.select_option(label=option.inner_text())
#     #                     break
#     #     except:
#     #         pass
#     #
#     # # === Custom comboboxes (role="combobox") ===
#     # comboboxes = page.query_selector_all('[role="combobox"]')
#     # for box in comboboxes:
#     #     try:
#     #         label = box.evaluate("el => el.closest('label')?.innerText || el.closest('div')?.innerText || ''")
#     #         value = get_resume_value(label)
#     #         if value:
#     #             box.click()
#     #             page.keyboard.type(str(value))
#     #             page.keyboard.press("Enter")
#     #     except:
#     #         pass
#     #
#     # # === Radio buttons ===
#     # radio_buttons = page.query_selector_all('input[type="radio"]')
#     # for radio in radio_buttons:
#     #     try:
#     #         label = radio.evaluate("el => el.closest('label')?.innerText || ''")
#     #         value = get_resume_value(label)
#     #         if value and value.lower() in label.lower():
#     #             radio.check()
#     #     except:
#     #         pass
#     #
#     # # === Checkboxes ===
#     # checkboxes = page.query_selector_all('input[type="checkbox"]')
#     # for checkbox in checkboxes:
#     #     try:
#     #         label = checkbox.evaluate("el => el.closest('label')?.innerText || ''")
#     #         if any(word in label.lower() for word in ["agree", "confirm", "consent", "accept", "yes"]):
#     #             checkbox.check()
#     #     except:
#     #         pass
#
#
# def main():
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         context = browser.new_context()
#         page = context.new_page()
#
#         login_to_linkedin(page)
#         search_jobs(page,job_title=TARGET_JOB_TITLE,job_location=TARGET_LOCATION)
#         filter_easy_apply_jobs(page)
#
#
#         context.close()
#         browser.close()
#
# # Run the main function
# if __name__ == "__main__":
#     main()
#
#



####################################################################################################
# import json
# from playwright.sync_api import sync_playwright
# import csv
# import os
# import requests
#
# # Load config.json
# with open("config.json", "r") as f:
#     config = json.load(f)
#
# LINKEDIN_USERNAME = config["LINKEDIN_USERNAME"]
# LINKEDIN_PASSWORD = config["LINKEDIN_PASSWORD"]
# RESUME_PATH = config["resume_path"]
# TARGET_JOB_TITLE = config["target_job_title"]
# TARGET_LOCATION = config["target_location"]
# LOG_FILE_PATH = config["log_file_path"]
# MAX_JOBS_PER_RUN = config.get("max_jobs_per_run", 5)
#
# OLLAMA_API_URL = config["LLM_API_URL"]
#
# def login_to_linkedin(page):
#     page.goto("https://www.linkedin.com/login")
#     page.fill('input#username', LINKEDIN_USERNAME)
#     page.fill('input#password', LINKEDIN_PASSWORD)
#     page.click('button[type="submit"]')
#     page.wait_for_url("https://www.linkedin.com/feed/")
#     print("✅ Logged in Successfully")
#
# def search_jobs(page, job_title, job_location):
#     page.goto("https://www.linkedin.com/jobs/")
#     if job_title:
#         title_input = page.locator('//input[@aria-label="Search by title, skill, or company"]').first
#         title_input.click()
#         title_input.fill(job_title)
#         print("🔍 Entered Job Title")
#     if job_location:
#         try:
#             location_input = page.locator('//input[@aria-label="City, state, or zip code"]').first
#             location_input.wait_for(state="visible")
#             location_input.click()
#             location_input.press("Control+A")
#             location_input.press("Backspace")
#             location_input.fill(job_location)
#             page.wait_for_selector("ul[role='listbox'] li")
#             page.keyboard.press("ArrowDown")
#             page.keyboard.press("Enter")
#             page.wait_for_timeout(3000)
#             print("📍 Filled Job Location")
#         except Exception as e:
#             print("❌ Error entering job location:", e)
#
# def filter_easy_apply_jobs(page):
#     try:
#         filter_btn = page.locator("button:has-text('Easy Apply')").first
#         filter_btn.click()
#         print("🧠 Filtered to Easy Apply jobs")
#         page.wait_for_timeout(3000)
#     except Exception as e:
#         print("❌ Easy Apply filter error:", e)
#
# # def get_llm_answer(prompt):
# #     try:
# #         response = requests.post(OLLAMA_API_URL, json={
# #             "messages": [{"role": "user", "content": prompt}],
# #             "model": "llama3"
# #         })
# #         if response.status_code == 200:
# #             return response.json()['choices'][0]['message']['content']
# #     except Exception as e:
# #         print("❌ LLM Error:", e)
# #     return ""
#
# import requests
#
# def get_llm_answer(prompt):
#     response = requests.post("http://localhost:11434/api/chat", json={
#         "model": "llama3",
#         "messages": [{"role": "user", "content": prompt}]
#     })
#     return response.json()['message']['content'].strip()
#
#
# def get_label_for_field(field):
#     return field.evaluate("""
#     el => {
#         const id = el.id;
#         if (id) {
#             const label = document.querySelector(`label[for="${id}"]`);
#             if (label) return label.innerText.trim();
#         }
#         const parentLabel = el.closest('label');
#         if (parentLabel) return parentLabel.innerText.trim();
#         return el.getAttribute('aria-label') || el.getAttribute('placeholder') || '';
#     }
#     """)
#
# def print_all_field_labels(page):
#     form_container = page.query_selector(".jobs-easy-apply-modal")
#     if not form_container:
#         print("⚠️ No Easy Apply form found.")
#         return
#
#     print("\n📋 All Field Labels:\n" + "-" * 40)
#
#     all_fields = form_container.query_selector_all("input, textarea, select")
#     for field in all_fields:
#         try:
#             label = get_label_for_field(field)
#             if label:
#                 print(f"• {label}")
#         except Exception as e:
#             print(f"❌ Error reading label: {e}")
#
#
# def fill_all_fields_on_page(page):
#     form_container = page.query_selector(".jobs-easy-apply-modal")
#     if not form_container:
#         print("⚠️ No Easy Apply form found.")
#         return
#
#     text_fields = form_container.query_selector_all("input:not([type=hidden]):not([readonly]):not([type=checkbox]):not([type=radio]), textarea")
#     for field in text_fields:
#         try:
#             label = get_label_for_field(field)
#             if not label or any(kw in label.lower() for kw in ["search", "title, skill", "company"]):
#                 continue
#             current_value = field.input_value().strip()
#             if current_value:
#                 print(f"\n📝 Text Field:\n- Label : {label}\n- Answer: {current_value} (Already filled)")
#
#             else:
#                 prompt = f"Please provide a professional answer to the job application question: '{label}'"
#                 answer = get_llm_answer(prompt).strip()
#                 field.fill(answer)
#                 print(f"\n📝 Text Field:\n- Label : {label}\n- Answer: {answer} (Filled now)")
#         except Exception as e:
#             print(f"❌ Text field error: {e}")
#
#     for dropdown in page.query_selector_all("select"):
#         try:
#             label = get_label_for_field(dropdown)
#             if not label:
#                 continue
#             selected_value = dropdown.input_value()
#             if selected_value:
#                 selected_option = dropdown.query_selector(f"option[value='{selected_value}']")
#                 print(f"\n🔽 Dropdown:\n- Label : {label}\n- Answer: {selected_option.inner_text().strip()} (Already selected)")
#             else:
#                 prompt = f"Choose the best option for: '{label}'. Only reply with the exact option text."
#                 answer = get_llm_answer(prompt).strip()
#                 for option in dropdown.query_selector_all("option"):
#                     if answer.lower() in option.inner_text().strip().lower():
#                         dropdown.select_option(label=option.inner_text().strip())
#                         print(f"\n🔽 Dropdown:\n- Label : {label}\n- Answer: {option.inner_text().strip()} (Filled now)")
#                         break
#         except Exception as e:
#             print(f"❌ Dropdown error: {e}")
#
#     for radio in page.query_selector_all("input[type=radio]"):
#         try:
#             label = get_label_for_field(radio)
#             name = radio.get_attribute("name")
#             if not label or not name:
#                 continue
#             if radio.is_checked():
#                 print(f"\n🔘 Radio Button:\n- Label : {label}\n- Answer: Selected (Already selected)")
#             else:
#                 prompt = f"Should the option '{label}' be selected for the question '{name}'? Reply Yes or No."
#                 if "yes" in get_llm_answer(prompt).strip().lower():
#                     radio.check(force=True)
#                     print(f"\n🔘 Radio Button:\n- Label : {label}\n- Answer: Selected (Filled now)")
#         except Exception as e:
#             print(f"❌ Radio button error: {e}")
#
#     for checkbox in page.query_selector_all("input[type=checkbox]"):
#         try:
#             label = get_label_for_field(checkbox)
#             if not label:
#                 continue
#             if checkbox.is_checked():
#                 print(f"\n☑️ Checkbox:\n- Label : {label}\n- Answer: Checked (Already checked)")
#             else:
#                 prompt = f"Should this checkbox be selected: '{label}'? Reply Yes or No."
#                 if "yes" in get_llm_answer(prompt).strip().lower():
#                     checkbox.check(force=True)
#                     print(f"\n☑️ Checkbox:\n- Label : {label}\n- Answer: Checked (Checked now)")
#         except Exception as e:
#             print(f"❌ Checkbox error: {e}")
#
# def save_to_csv(data, filename):
#     file_exists = os.path.isfile(filename)
#     with open(filename, mode='a', newline='', encoding='utf-8') as file:
#         writer = csv.DictWriter(file, fieldnames=["Job Title", "Company Name", "Location", "Job Description"])
#         if not file_exists:
#             writer.writeheader()
#         for row in data:
#             writer.writerow(row)
#
# def apply_to_jobs(page):
#     applied_jobs = []
#     job_cards = page.query_selector_all("div.job-card-container")
#     for idx, job in enumerate(job_cards):
#         try:
#             job.click()
#             page.wait_for_timeout(3000)
#             apply_btn = page.query_selector("button.jobs-apply-button")
#             if not apply_btn:
#                 print("⏭️ Skipping non-Easy Apply job")
#                 continue
#
#             job_title = page.query_selector("h2.topcard__title") or page.query_selector("h1")
#             company = page.query_selector("a.topcard__org-name-link") or page.query_selector("span.topcard__flavor")
#             location = page.query_selector("span.jobs-unified-top-card__bullet")
#             description = page.query_selector("div.job-details-module.jobs-description")
#
#             apply_btn.click()
#             page.wait_for_timeout(2000)
#
#             while True:
#                 page.wait_for_timeout(1000)
#                 fill_all_fields_on_page(page)
#
#                 if (submit := page.query_selector("button:has-text('Submit')")) and submit.is_enabled():
#                     submit.click()
#                     page.wait_for_timeout(3000)
#                     if (done := page.locator("button:has-text('Done')")):
#                         done.click()
#                     print("✅ Application submitted")
#                     break
#                 elif (review := page.query_selector("button:has-text('Review')")) and review.is_enabled():
#                     review.click()
#                 elif (next_btn := page.query_selector("button:has-text('Next')")) and next_btn.is_enabled():
#                     next_btn.click()
#                 else:
#                     break
#
#             applied_jobs.append({
#                 "Job Title": job_title.inner_text().strip() if job_title else "",
#                 "Company Name": company.inner_text().strip() if company else "",
#                 "Location": location.inner_text().strip() if location else "",
#                 "Job Description": description.inner_text().strip() if description else ""
#             })
#         except Exception as e:
#             print(f"❌ Error in job #{idx + 1}: {e}")
#     return applied_jobs
#
# def main():
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         context = browser.new_context()
#         page = context.new_page()
#
#         login_to_linkedin(page)
#         search_jobs(page, TARGET_JOB_TITLE, TARGET_LOCATION)
#         filter_easy_apply_jobs(page)
#         jobs_applied = apply_to_jobs(page)
#         save_to_csv(jobs_applied, LOG_FILE_PATH)
#         print("✅ All done!")
#
# if __name__ == "__main__":
#     main()


################################################ollama+webui###########################################
#
# import json
# from playwright.sync_api import sync_playwright
# import csv
# import os
# import requests   # <-- Add this if not already there
#
# # Load config.json
# # Load config once at the start
# with open("config.json", "r") as f:
#     config = json.load(f)
#
# api_url = config["llm_api_url"]
# model = config["llm_model"]
# LINKEDIN_USERNAME = config["LINKEDIN_USERNAME"]
# LINKEDIN_PASSWORD = config["LINKEDIN_PASSWORD"]
# RESUME_PATH = config["resume_path"]
# TARGET_JOB_TITLE = config["target_job_title"]
# TARGET_LOCATION = config["target_location"]
# LOG_FILE_PATH = config["log_file_path"]
# MAX_JOBS_PER_RUN = config.get("max_jobs_per_run", 5)
#
# # ====== Add your generate_answer_with_llm here ======
# import requests
#
# def generate_answer_with_llm(question):
#     payload = {
#         "model": model,
#         "prompt": f"Question: {question}",
#         "temperature": 0.2
#     }
#
#     try:
#         response = requests.post(api_url, json=payload)
#         response.raise_for_status()
#         result = response.json()
#         answer = result['response'].strip()
#         print(f"💬 Q: {question}\n👉 A: {answer}")
#         return answer
#     except Exception as e:
#         print(f"LLM Error: {e}")
#         print(f"Response content: {response.text}")
#         return ""
#
#
# def login_to_linkedin(page):
#     # Go to LinkedIn login page
#     page.goto("https://www.linkedin.com/login")
#
#     # Fill in credentials
#     page.fill('input#username', LINKEDIN_USERNAME)
#     page.fill('input#password', LINKEDIN_PASSWORD)
#
#     # Click login
#     page.click('button[type="submit"]')
#
#     try:
#         page.wait_for_url("https://www.linkedin.com/feed/", timeout=30000)
#         print("Logged in Successfully")
#     except:
#         page.screenshot(path="login_failed.png")
#         print("Login failed. Check credentials or captcha requirement.")
#         page.wait_for_timeout(10000)  # Pause 10 seconds before closing
#
# def search_jobs(page,job_title=TARGET_JOB_TITLE,job_location=TARGET_LOCATION):
#     # Go to the LinkedIn Jobs section
#     page.goto("https://www.linkedin.com/jobs/")
#     if job_title:
#         try:
#             title_input = page.locator('//input[@aria-label="Search by title, skill, or company"]').first
#             title_input.wait_for(state="visible", timeout=20000)
#             title_input.click()
#             title_input.fill(job_title)
#             print("Enter Job Title")
#         except Exception as e:
#             print("Error entering job title:", e)
#
#     if job_location:
#         try:
#             location_input = page.locator('//input[@aria-label="City, state, or zip code"]').first
#             location_input.wait_for(state="visible", timeout=15000)
#             location_input.click()
#             location_input.press("Control+A")
#             location_input.press("Backspace")
#             location_input.fill(job_location)
#
#             # Wait for LinkedIn's autocomplete dropdown to appear
#             page.wait_for_selector("ul[role='listbox'] li", timeout=5000)
#
#             # Now press ArrowDown + Enter to select the first suggestion
#             page.keyboard.press("ArrowDown")
#             page.keyboard.press("Enter")
#
#             page.wait_for_timeout(5000)  # Let the page settle
#             print("Filled Job Location")
#         except Exception as e:
#             print("Error entering job location:", e)
#
#
# def filter_easy_apply_jobs(page):
#     applied_jobs = []
#
#     try:
#         filter_btn = page.locator("button:has-text('Easy Apply')").first
#         filter_btn.click()
#         print("Filtered to Easy Apply jobs")
#         page.wait_for_timeout(3000)
#     except Exception as e:
#         print("Easy Apply filter error:", e)
#
#     page.wait_for_selector("div.job-card-container", timeout=10000)
#     jobs = page.query_selector_all("div.job-card-container")
#
#     for idx, job in enumerate(jobs):
#         try:
#             job.click()
#             page.wait_for_timeout(3000)
#
#             apply_btn = page.query_selector("button.jobs-apply-button")
#             if not apply_btn:
#                 print("Skipping non-Easy Apply job")
#                 continue
#
#             # Extract job info BEFORE clicking apply
#             job_title = page.query_selector("h2.topcard__title") or page.query_selector("h1")
#             # # company_name = page.query_selector("span.topcard__flavor")
#             # company_name = page.query_selector("a.topcard__org-name-link") or page.query_selector("span.topcard__flavor")
#             # # location = page.query_selector("span.topcard__flavor--bullet")
#             # location = page.query_selector("span.jobs-unified-top-card__bullet") or page.query_selector("span.topcard__flavor--bullet")
#             # ✅ Company Name
#             company_name = (
#                     page.query_selector("a.topcard__org-name-link") or
#                     page.query_selector("span.topcard__flavor") or
#                     page.query_selector("div.artdeco-entity-lockup__subtitle")
#             )
#
#             # ✅ Location
#             location = (
#                     page.query_selector("span.jobs-unified-top-card__bullet") or
#                     page.query_selector("span.topcard__flavor--bullet") or
#                     page.query_selector("div.artdeco-entity-lockup__caption")
#             )
#             job.click()
#             page.wait_for_timeout(5000)
#             right_panel = page.query_selector("div.jobs-details") or page.query_selector("div.jobs-search__job-details")
#             if right_panel:
#                 right_panel.scroll_into_view_if_needed()
#                 page.mouse.wheel(0, 5000)
#                 page.wait_for_timeout(2000)
#
#             # job_description = page.query_selector("div.description__text")
#             job_description = (
#                     # page.query_selector("div.show-more-less-html__markup")
#                     # page.query_selector("div.description__text")
#                     # page.query_selector("article.jobs-description__container")
#                     # page.query_selector("div.jobs-description--reformatted") or
#                     page.query_selector("div.job-details-module.jobs-description")
#             )
#
#             title_text = job_title.inner_text().strip() if job_title else "N/A"
#             company_text = company_name.inner_text().strip() if company_name else "N/A"
#             location_text = location.inner_text().strip() if location else "N/A"
#             desc_text = job_description.inner_text().strip() if job_description else "N/A"
#
#             apply_btn.click()
#             page.wait_for_timeout(2000)
#
#             while True:
#                 page.wait_for_timeout(1000)
#
#                 fill_all_fields_on_page(page)  # your form filler
#
#                 next_btn = page.query_selector("button:has-text('Next')")
#                 review_btn = page.query_selector("button:has-text('Review')")
#                 submit_btn = page.query_selector("button:has-text('Submit')")
#
#                 if submit_btn and submit_btn.is_enabled():
#                     submit_btn.click()
#                     print("Application Submitted!")
#                     page.wait_for_timeout(3000)
#                     try:
#                         # Wait for the Done button to appear
#                         done_button = page.locator("button:has-text('Done')")
#                         done_button.wait_for(timeout=5000)  # wait up to 5 seconds
#                         done_button.click()
#                         print("Application submitted and 'Done' button clicked.")
#                     except Exception as e:
#                         print("Done button not found or not clickable:", e)
#
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
#
#             print(f"Applied to job #{idx + 1}: {page.url}")
#
#             applied_jobs.append({
#                 "Job Title": title_text,
#                 "Company Name": company_text,
#                 "Location": location_text,
#                 "Job Description": desc_text,
#             })
#
#             page.wait_for_timeout(3000)
#
#         except Exception as e:
#             print(f"Error in job #{idx + 1}: {e}")
#             continue
#
#     # Save to CSV
#     save_to_csv(applied_jobs)
#     print(f"Total jobs applied: {len(applied_jobs)}")
#
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
# def fill_all_fields_on_page(page):
#     file_inputs = page.query_selector_all("input[type='file']")
#     for file_input in file_inputs:
#         try:
#             file_input.set_input_files(RESUME_PATH)
#             print(f"📎 Uploaded resume from {RESUME_PATH}")
#         except Exception as e:
#             print(f"Resume upload failed: {e}")
#
#     text_fields = page.query_selector_all("input:not([type=hidden]):not([readonly]), textarea")
#     for field in text_fields:
#         try:
#             label = field.evaluate("el => el.closest('label')?.innerText || el.getAttribute('aria-label') || ''")
#             if label:
#                 answer = generate_answer_with_llm(label)
#                 if answer:
#                     field.fill(answer)
#         except Exception as e:
#             print(f"Error filling text field: {e}")
#
#     dropdowns = page.query_selector_all("select")
#     for dropdown in dropdowns:
#         try:
#             label = dropdown.evaluate("el => el.closest('label')?.innerText || el.getAttribute('aria-label') || ''")
#             if label:
#                 answer = generate_answer_with_llm(label)
#                 if answer:
#                     options = dropdown.query_selector_all("option")
#                     for option in options:
#                         if answer.lower() in option.inner_text().strip().lower():
#                             dropdown.select_option(label=option.inner_text())
#                             break
#         except Exception as e:
#             print(f"Error filling dropdown: {e}")
#
#     comboboxes = page.query_selector_all('[role="combobox"]')
#     for box in comboboxes:
#         try:
#             label = box.evaluate("el => el.closest('label')?.innerText || el.getAttribute('aria-label') || ''")
#             if label:
#                 answer = generate_answer_with_llm(label)
#                 if answer:
#                     box.click()
#                     page.keyboard.type(answer)
#                     page.keyboard.press("Enter")
#         except Exception as e:
#             print(f"Error filling combobox: {e}")
#
#     radio_buttons = page.query_selector_all('input[type="radio"]')
#     for radio in radio_buttons:
#         try:
#             label = radio.evaluate("el => el.closest('label')?.innerText || ''")
#             if label:
#                 answer = generate_answer_with_llm(label)
#                 if answer.lower() in label.lower():
#                     radio.check()
#         except Exception as e:
#             print(f"Error checking radio: {e}")
#
#     checkboxes = page.query_selector_all('input[type="checkbox"]')
#     for checkbox in checkboxes:
#         try:
#             label = checkbox.evaluate("el => el.closest('label')?.innerText || ''")
#             if label and any(word in label.lower() for word in ["agree", "confirm", "consent", "accept", "yes"]):
#                 checkbox.check()
#         except Exception as e:
#             print(f"Error checking checkbox: {e}")
#
#
# def main():
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         context = browser.new_context()
#         page = context.new_page()
#
#         login_to_linkedin(page)
#         search_jobs(page,job_title=TARGET_JOB_TITLE,job_location=TARGET_LOCATION)
#         filter_easy_apply_jobs(page)
#
#
#         context.close()
#         browser.close()
#
# # Run the main function
# if __name__ == "__main__":
#     main()
#
#
#
#

##################################ollama + webui##################################################################################
#
# import json
# import csv
# import os
# import requests
# from playwright.sync_api import sync_playwright
#
# # Load config.json
# with open("config.json", "r") as f:
#     config = json.load(f)
#
# LINKEDIN_USERNAME = config["LINKEDIN_USERNAME"]
# LINKEDIN_PASSWORD = config["LINKEDIN_PASSWORD"]
# RESUME_PATH = config["resume_path"]
# TARGET_JOB_TITLE = config["target_job_title"]
# TARGET_LOCATION = config["target_location"]
# LOG_FILE_PATH = config["log_file_path"]
# OLLAMA_API_URL = config["OLLAMA_API"]
# # OLLAMA_API_URL = config.get("ollama_api_url", "http://localhost:3000/api/chat/completions")
#
# OLLAMA_MODEL = config.get("ollama_model", "llama3")
# MAX_JOBS_PER_RUN = config.get("max_jobs_per_run", 5)
#
# # def ask_llm(prompt):
# #     payload = {
# #         "model": OLLAMA_MODEL,
# #         "messages": [{"role": "user", "content": prompt}],
# #         "stream": False,
# #     }
# #     try:
# #         response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
# #         if response.status_code == 200:
# #             data = response.json()
# #             return data["choices"][0]["message"]["content"].strip()
# #         else:
# #             print(f"LLM Error {response.status_code}: {response.text}")
# #             return ""
# #     except Exception as e:
# #         print(f"Error contacting LLM: {e}")
# #         return ""
#
# def ask_llm(prompt):
#     payload = {
#         "model": OLLAMA_MODEL,
#         "messages": [{"role": "user", "content": prompt}],
#         "stream": False,
#     }
#     try:
#         response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
#         if response.status_code == 200:
#             data = response.json()
#             # Print full response to debug
#             print(f"LLM Response: {data}")
#             # Check if 'choices' exists and has expected content
#             if "choices" in data and len(data["choices"]) > 0:
#                 return data["choices"][0]["message"]["content"].strip()
#             else:
#                 print(f"Error: 'choices' not found in response or empty.")
#                 return ""
#         else:
#             print(f"LLM Error {response.status_code}: {response.text}")
#             return ""
#     except Exception as e:
#         print(f"Error contacting LLM: {e}")
#         return ""
#
#
# def login_to_linkedin(page):
#     page.goto("https://www.linkedin.com/login")
#     page.fill('input#username', LINKEDIN_USERNAME)
#     page.fill('input#password', LINKEDIN_PASSWORD)
#     page.click('button[type="submit"]')
#     try:
#         page.wait_for_url("https://www.linkedin.com/feed/", timeout=30000)
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
#
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
# def filter_easy_apply_jobs(page):
#     applied_jobs = []
#     try:
#         filter_btn = page.locator("button:has-text('Easy Apply')").first
#         filter_btn.click()
#         print("Filtered to Easy Apply jobs")
#         page.wait_for_timeout(3000)
#     except Exception as e:
#         print("Easy Apply filter error:", e)
#
#     page.wait_for_selector("div.job-card-container", timeout=10000)
#     jobs = page.query_selector_all("div.job-card-container")
#
#     for idx, job in enumerate(jobs):
#         try:
#             job.click()
#             page.wait_for_timeout(3000)
#             apply_btn = page.query_selector("button.jobs-apply-button")
#             if not apply_btn:
#                 print("Skipping non-Easy Apply job")
#                 continue
#
#             job_title = page.query_selector("h2.topcard__title") or page.query_selector("h1")
#             company_name = page.query_selector("a.topcard__org-name-link") or page.query_selector("span.topcard__flavor")
#             location = page.query_selector("span.jobs-unified-top-card__bullet") or page.query_selector("span.topcard__flavor--bullet")
#             job_description = page.query_selector("div.job-details-module.jobs-description")
#
#             title_text = job_title.inner_text().strip() if job_title else "N/A"
#             company_text = company_name.inner_text().strip() if company_name else "N/A"
#             location_text = location.inner_text().strip() if location else "N/A"
#             desc_text = job_description.inner_text().strip() if job_description else "N/A"
#
#             apply_btn.click()
#             page.wait_for_timeout(2000)
#
#             while True:
#                 page.wait_for_timeout(1000)
#                 fill_all_fields_on_page(page)
#
#                 next_btn = page.query_selector("button:has-text('Next')")
#                 review_btn = page.query_selector("button:has-text('Review')")
#                 submit_btn = page.query_selector("button:has-text('Submit')")
#
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
#
#             applied_jobs.append({
#                 "Job Title": title_text,
#                 "Company Name": company_text,
#                 "Location": location_text,
#                 "Job Description": desc_text,
#             })
#
#             page.wait_for_timeout(3000)
#
#         except Exception as e:
#             print(f"Error in job #{idx + 1}: {e}")
#             continue
#
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
# def fill_all_fields_on_page(page):
#     file_inputs = page.query_selector_all("input[type='file']")
#     for file_input in file_inputs:
#         try:
#             file_input.set_input_files(RESUME_PATH)
#             print(f"📎 Uploaded resume: {RESUME_PATH}")
#         except Exception as e:
#             print(f"Resume upload failed: {e}")
#
#     text_fields = page.query_selector_all("input:not([type=hidden]):not([readonly]), textarea")
#     for field in text_fields:
#         try:
#             label = field.evaluate("el => el.closest('label')?.innerText || el.closest('div')?.innerText || ''")
#             if label:
#                 question = f"Answer this job application field briefly and professionally: '{label}'"
#                 answer = ask_llm(question)
#                 if answer:
#                     print(f"Filling '{label}' with: {answer}")
#                     field.fill(answer)
#         except Exception as e:
#             print(f"Error filling text field: {e}")
#
#     dropdowns = page.query_selector_all("select")
#     for dropdown in dropdowns:
#         try:
#             label = dropdown.evaluate("el => el.closest('label')?.innerText || el.closest('div')?.innerText || ''")
#             if label:
#                 question = f"Select appropriate short answer for: '{label}' (must match dropdown option)"
#                 answer = ask_llm(question)
#                 if answer:
#                     options = dropdown.query_selector_all("option")
#                     for option in options:
#                         if answer.lower() in option.inner_text().strip().lower():
#                             dropdown.select_option(label=option.inner_text())
#                             print(f"Selected '{answer}' for '{label}'")
#                             break
#         except Exception as e:
#             print(f"Error selecting dropdown: {e}")
#
#     comboboxes = page.query_selector_all('[role="combobox"]')
#     for box in comboboxes:
#         try:
#             label = box.evaluate("el => el.closest('label')?.innerText || el.closest('div')?.innerText || ''")
#             if label:
#                 question = f"Provide a brief value for: '{label}'"
#                 answer = ask_llm(question)
#                 if answer:
#                     box.click()
#                     page.keyboard.type(answer)
#                     page.keyboard.press("Enter")
#         except Exception as e:
#             print(f"Error filling combobox: {e}")
#
#     radio_buttons = page.query_selector_all('input[type="radio"]')
#     for radio in radio_buttons:
#         try:
#             label = radio.evaluate("el => el.closest('label')?.innerText || ''")
#             if label:
#                 question = f"Should I select '{label}' in a job application? Answer Yes or No."
#                 answer = ask_llm(question)
#                 if "yes" in answer.lower():
#                     radio.check()
#         except Exception as e:
#             print(f"Error checking radio: {e}")
#
#     checkboxes = page.query_selector_all('input[type="checkbox"]')
#     for checkbox in checkboxes:
#         try:
#             label = checkbox.evaluate("el => el.closest('label')?.innerText || ''")
#             if label and any(word in label.lower() for word in ["agree", "confirm", "consent", "accept", "yes"]):
#                 checkbox.check()
#         except Exception as e:
#             print(f"Error checking checkbox: {e}")
#
# def main():
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         context = browser.new_context()
#         page = context.new_page()
#         login_to_linkedin(page)
#         search_jobs(page)
#         filter_easy_apply_jobs(page)
#         context.close()
#         browser.close()
#
# if __name__ == "__main__":
#     main()

#
# import json
# import csv
# import os
# import requests
# from playwright.sync_api import sync_playwright
#
# # Load config.json
# with open("config.json", "r") as f:
#     config = json.load(f)
#
# LINKEDIN_USERNAME = config["LINKEDIN_USERNAME"]
# LINKEDIN_PASSWORD = config["LINKEDIN_PASSWORD"]
# RESUME_PATH = config["resume_path"]
# TARGET_JOB_TITLE = config["target_job_title"]
# TARGET_LOCATION = config["target_location"]
# LOG_FILE_PATH = config["log_file_path"]
# OLLAMA_API_URL = config["OLLAMA_API"]
# OLLAMA_MODEL = config.get("ollama_model", "llama3")
# MAX_JOBS_PER_RUN = config.get("max_jobs_per_run", 5)
#
# def ask_llm(prompt):
#     payload = {
#         "model": OLLAMA_MODEL,
#         "messages": [{"role": "user", "content": prompt}],
#         "stream": False,
#
#     }
#     print(f"Sending request to {OLLAMA_API_URL} with payload: {payload}")  # Add this log
#     try:
#         response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
#         if response.status_code == 200:
#             data = response.json()
#             print(f"LLM Response: {data}")
#             if "choices" in data and len(data["choices"]) > 0:
#                 return data["choices"][0]["message"]["content"].strip()
#             else:
#                 print("Error: 'choices' not found in response or empty.")
#                 return ""
#         else:
#             print(f"LLM Error {response.status_code}: {response.text}")
#             return ""
#     except Exception as e:
#         print(f"Error contacting LLM: {e}")
#         return ""
#
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
# def filter_easy_apply_jobs(page):
#     applied_jobs = []
#     try:
#         filter_btn = page.locator("button:has-text('Easy Apply')").first
#         filter_btn.click()
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
#             company_name = page.query_selector("a.topcard__org-name-link") or page.query_selector("span.topcard__flavor")
#             location = page.query_selector("span.jobs-unified-top-card__bullet") or page.query_selector("span.topcard__flavor--bullet")
#             job_description = page.query_selector("div.job-details-module.jobs-description")
#             title_text = job_title.inner_text().strip() if job_title else "N/A"
#             company_text = company_name.inner_text().strip() if company_name else "N/A"
#             location_text = location.inner_text().strip() if location else "N/A"
#             desc_text = job_description.inner_text().strip() if job_description else "N/A"
#             apply_btn.click()
#             page.wait_for_timeout(2000)
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
# def fill_all_fields_on_page(page):
#     file_inputs = page.query_selector_all("input[type='file']")
#     for file_input in file_inputs:
#         try:
#             file_input.set_input_files(RESUME_PATH)
#             print(f"\ud83d\udcce Uploaded resume: {RESUME_PATH}")
#         except Exception as e:
#             print(f"Resume upload failed: {e}")
#     text_fields = page.query_selector_all("input:not([type=hidden]):not([readonly]), textarea")
#     for field in text_fields:
#         try:
#             label = field.evaluate("el => el.closest('label')?.innerText || el.closest('div')?.innerText || ''")
#             if label:
#                 question = f"Answer this job application field briefly and professionally: '{label}'"
#                 answer = ask_llm(question)
#                 if answer:
#                     print(f"Filling '{label}' with: {answer}")
#                     field.fill(answer)
#         except Exception as e:
#             print(f"Error filling text field: {e}")
#     dropdowns = page.query_selector_all("select")
#     for dropdown in dropdowns:
#         try:
#             label = dropdown.evaluate("el => el.closest('label')?.innerText || el.closest('div')?.innerText || ''")
#             if label:
#                 question = f"Select appropriate short answer for: '{label}' (must match dropdown option)"
#                 answer = ask_llm(question)
#                 if answer:
#                     options = dropdown.query_selector_all("option")
#                     for option in options:
#                         if answer.lower() in option.inner_text().strip().lower():
#                             dropdown.select_option(label=option.inner_text())
#                             print(f"Selected '{answer}' for '{label}'")
#                             break
#         except Exception as e:
#             print(f"Error selecting dropdown: {e}")
#     comboboxes = page.query_selector_all('[role="combobox"]')
#     for box in comboboxes:
#         try:
#             label = box.evaluate("el => el.closest('label')?.innerText || el.closest('div')?.innerText || ''")
#             if label:
#                 question = f"Provide a brief value for: '{label}'"
#                 answer = ask_llm(question)
#                 if answer:
#                     box.click()
#                     page.keyboard.type(answer)
#                     page.keyboard.press("Enter")
#         except Exception as e:
#             print(f"Error filling combobox: {e}")
#     radio_buttons = page.query_selector_all('input[type="radio"]')
#     for radio in radio_buttons:
#         try:
#             label = radio.evaluate("el => el.closest('label')?.innerText || ''")
#             if label:
#                 question = f"Should I select '{label}' in a job application? Answer Yes or No."
#                 answer = ask_llm(question)
#                 if "yes" in answer.lower():
#                     radio.check()
#         except Exception as e:
#             print(f"Error checking radio: {e}")
#     checkboxes = page.query_selector_all('input[type="checkbox"]')
#     for checkbox in checkboxes:
#         try:
#             label = checkbox.evaluate("el => el.closest('label')?.innerText || ''")
#             if label and any(word in label.lower() for word in ["agree", "confirm", "consent", "accept", "yes"]):
#                 checkbox.check()
#         except Exception as e:
#             print(f"Error checking checkbox: {e}")
#
# with sync_playwright() as p:
#     browser = p.chromium.launch(headless=False)
#     page = browser.new_page()
#     login_to_linkedin(page)
#     search_jobs(page)
#     filter_easy_apply_jobs(page)
#     browser.close()





import json
import csv
import os
import requests
from playwright.sync_api import sync_playwright

#Load config.json
with open("config.json", "r") as f:
    config = json.load(f)

LINKEDIN_USERNAME = config["LINKEDIN_USERNAME"]
LINKEDIN_PASSWORD = config["LINKEDIN_PASSWORD"]
RESUME_PATH = config["resume_path"]
TARGET_JOB_TITLE = config["target_job_title"]
TARGET_LOCATION = config["target_location"]
LOG_FILE_PATH = config["log_file_path"]
OLLAMA_API_URL = config["OLLAMA_API"]
OLLAMA_MODEL = config["ollama_model"]
MAX_JOBS_PER_RUN = config.get("max_jobs_per_run", 5)

def ask_llm(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    print(f"Sending request to {OLLAMA_API_URL} with payload: {payload}")

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"LLM Response: {data}")
            return data.get("response", "").strip()
        else:
            print(f"LLM Error {response.status_code}: {response.text}")
            return ""
    except Exception as e:
        print(f"Error contacting LLM: {e}")
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

def filter_easy_apply_jobs(page):
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
            company_name = page.query_selector("a.topcard__org-name-link") or page.query_selector("span.topcard__flavor")
            location = page.query_selector("span.jobs-unified-top-card__bullet") or page.query_selector("span.topcard__flavor--bullet")
            job_description = page.query_selector("div.job-details-module.jobs-description")
            title_text = job_title.inner_text().strip() if job_title else "N/A"
            company_text = company_name.inner_text().strip() if company_name else "N/A"
            location_text = location.inner_text().strip() if location else "N/A"
            desc_text = job_description.inner_text().strip() if job_description else "N/A"
            apply_btn.click()
            page.wait_for_timeout(2000)
            while True:
                page.wait_for_timeout(1000)
                fill_all_fields_on_page(page)
                next_btn = page.query_selector("button:has-text('Next')")
                review_btn = page.query_selector("button:has-text('Review')")
                submit_btn = page.query_selector("button:has-text('Submit')")
                if submit_btn and submit_btn.is_enabled():
                    submit_btn.click()
                    print("Application Submitted!")
                    page.wait_for_timeout(3000)
                    try:
                        done_button = page.locator("button:has-text('Done')")
                        done_button.wait_for(timeout=5000)
                        done_button.click()
                        print("Clicked 'Done'")
                    except Exception as e:
                        print("Done button not found or error:", e)
                    break
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
    print(f"Total jobs applied: {len(applied_jobs)}")

def save_to_csv(data, filename="application_log.csv"):
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["Job Title", "Company Name", "Location", "Job Description"])
        if not file_exists:
            writer.writeheader()
        for row in data:
            writer.writerow(row)

def fill_all_fields_on_page(page):
    file_inputs = page.query_selector_all("input[type='file']")
    for file_input in file_inputs:
        try:
            file_input.set_input_files(RESUME_PATH)
            print(f"\ud83d\udcce Uploaded resume: {RESUME_PATH}")
        except Exception as e:
            print(f"Resume upload failed: {e}")
    text_fields = page.query_selector_all("input:not([type=hidden]):not([readonly]), textarea")
    for field in text_fields:
        try:
            label = field.evaluate("el => el.closest('label')?.innerText || el.closest('div')?.innerText || ''")
            if label:
                question = f"Answer this job application field briefly and professionally: '{label}'"
                answer = ask_llm(question)
                if answer:
                    print(f"Filling '{label}' with: {answer}")
                    field.fill(answer)
        except Exception as e:
            print(f"Error filling text field: {e}")
    dropdowns = page.query_selector_all("select")
    for dropdown in dropdowns:
        try:
            label = dropdown.evaluate("el => el.closest('label')?.innerText || el.closest('div')?.innerText || ''")
            if label:
                question = f"Select appropriate short answer for: '{label}' (must match dropdown option)"
                answer = ask_llm(question)
                if answer:
                    options = dropdown.query_selector_all("option")
                    for option in options:
                        if answer.lower() in option.inner_text().strip().lower():
                            dropdown.select_option(label=option.inner_text())
                            print(f"Selected '{answer}' for '{label}'")
                            break
        except Exception as e:
            print(f"Error selecting dropdown: {e}")
    comboboxes = page.query_selector_all('[role="combobox"]')
    for box in comboboxes:
        try:
            label = box.evaluate("el => el.closest('label')?.innerText || el.closest('div')?.innerText || ''")
            if label:
                question = f"Provide a brief value for: '{label}'"
                answer = ask_llm(question)
                if answer:
                    box.click()
                    page.keyboard.type(answer)
                    page.keyboard.press("Enter")
        except Exception as e:
            print(f"Error filling combobox: {e}")
    radio_buttons = page.query_selector_all('input[type="radio"]')
    for radio in radio_buttons:
        try:
            label = radio.evaluate("el => el.closest('label')?.innerText || ''")
            if label:
                question = f"Should I select '{label}' in a job application? Answer Yes or No."
                answer = ask_llm(question)
                if "yes" in answer.lower():
                    radio.check()
        except Exception as e:
            print(f"Error with radio button: {e}")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        login_to_linkedin(page)
        search_jobs(page)
        filter_easy_apply_jobs(page)
        browser.close()

if __name__ == "__main__":
    main()
