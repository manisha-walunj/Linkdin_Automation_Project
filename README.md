Setup & Configuration
from datetime import datetime
import time, json, csv, os, requests, re
from playwright.sync_api import sync_playwright
 Imports necessary libraries for:
•	Date/time, file I/O, HTTP requests, regex
•	Web automation via Playwright

def normalize(text): 

     return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', text.lower().strip()))
Cleans and standardizes strings for label matching.
(Clean label/question strings for reliable matching)

Load Configuration and Resume
with open("config.json", "r") as f:
    config = json.load(f)
with open("resume.txt", "r", encoding="utf-8") as file:
    resume_text = file.read()
Loads configuration values and resume content used by LLM.
Manual Answer Caching
load_manual_answers() / save_manual_answers()

(Avoid LLM calls for repeated questions)
These handle storing manually entered answers to application questions into a JSON file (manual_answers.json) to reuse them and avoid LLM/API overhead.

Resume Upload to LLM Server
upload_resume_get_file_id(RESUME_PATH)
(Get LLM-accessible resume reference)

Uploads the resume to OpenWebUI and returns a file ID to reference during LLM prompt construction.

Logging
log_application_data(...) 
Logs job metadata (title, company, location, description) and Q&A pairs into application_log.csv.
save_to_csv(data, filename="application_log.csv")
Appends job count and timestamp after a run.

Answer Generation
get_answer_from_llm(question, file_id, manual_answers)
(Smart/manual answer generation)


•	Reuses cached answer if available
•	If LLM is enabled, queries the model using resume + question
•	Falls back to manual input if LLM fails or is disabled

LinkedIn Automation Functions
login_to_linkedin(page)

(Authenticates into LinkedIn)

Logs into LinkedIn using credentials from config.json.
search_jobs(page, job_title, job_location)

(Filters job search results)
Fills in job title and location fields to filter search results.

filter_easy_apply_jobs(page, file_id, manual_answers)
(Automates Easy Apply job applications)
•	Filters jobs to “Easy Apply” only
•	Iterates through job cards
•	Extracts job info (title, company, location, description)
•	Clicks “Apply” button
•	Calls form filling functions
•	Handles final submission/review buttons
•	Logs applied jobs

Form Filling (Core Automation)
extract_and_fill_form_fields_across_steps(page, file_id, manual_answers)
(Multi-step form filling logic

•	Extracts all labeled and unlabeled form fields across modal steps
•	Checks if prefilled — skips if already filled
•	Queries LLM or uses cached/manual answers
•	Fills based on field type:
o	input (text, checkbox)
o	select (dropdown)
o	textarea
•	Handles navigation through multi-step forms
•	Logs each field/question with answer

fill_easy_apply_form_with_llm(page, file_id, manual_answers)
(LLM-based single-step form filling)


Simpler/fallback method to:
•	Extract all label elements
•	Query LLM and fill corresponding inputs based on label's for attribute or proximity

Main Execution(Entry point for the script)
main()
•	Launches Chromium via Playwright
•	Logs in to LinkedIn
•	Searches for jobs
•	Uploads resume
•	Filters Easy Apply jobs
•	Initiates auto-application process
•	Closes browser
if __name__ == "__main__":
    main()

















