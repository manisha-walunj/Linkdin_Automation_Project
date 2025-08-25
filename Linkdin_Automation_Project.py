
import csv
import os
import requests
from playwright.sync_api import sync_playwright
from urllib.parse import quote
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path, override=True)

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

def scroll_job_list(page, target_count=25):
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

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        login_to_linkedin(page)
        search_linkedin_jobs_with_combined_input(page, TARGET_JOB_TITLE, TARGET_LOCATION)
        file_id = upload_resume_get_file_id(RESUME_PATH)
        scroll_job_list(page, target_count=25)
        scrape_job_details(page, file_id, max_jobs=25)
        browser.close()


if __name__ == "__main__":
    main()