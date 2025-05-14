import time
import os
import csv
from datetime import datetime
import ollama
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
email = os.getenv("LINKEDIN_EMAIL")
password = os.getenv("LINKEDIN_PASSWORD")

# Job Search Parameters
job_title = "Python Developer Freshers"
location = "Navi Mumbai"

# Save applied job to CSV
def save_applied_job(company, role):
    filename = "applied_jobs.csv"
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["Company", "Role", "Applied At"])
        writer.writerow([company, role, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

# Check if job was already applied
# def already_applied(company, role):
#     filename = "applied_jobs.csv"
#     if not os.path.isfile(filename):
#         return False
#     with open(filename, mode='r', newline='', encoding='utf-8') as csvfile:
#         reader = csv.DictReader(csvfile)
#         for row in reader:
#             if row['Company'] == company and row['Role'] == role:
#                 return True
#     return False


def already_applied(company, role):
    try:
        with open('applied_jobs.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                print("Checking row:", row)  # Debug line
                if row['Company'] == company and row['Role'] == role:
                    return True
    except FileNotFoundError:
        print("CSV file not found. Skipping duplicate check.")
    except KeyError as e:
        print(f"KeyError: {e}. Check your CSV headers.")
    return False


# Use Ollama to generate a response
def generate_answer(label):
    response = ollama.chat(
        model="llama2",
        messages=[{"role": "user", "content": f"Provide an appropriate answer for a job application question: {label}"}]
    )
    return response['message']['content'].strip()

# Handle the Easy Apply form
# def handle_easy_apply(page):
#     print("\n📝 **Opening Easy Apply Form...**\n")
#
#     while True:
#         input_fields = page.locator("input, textarea")
#         for i in range(input_fields.count()):
#             field = input_fields.nth(i)
#             label = field.get_attribute("aria-label")
#
#             if label and field.is_enabled():
#                 current_value = field.input_value().strip()
#                 if current_value:
#                     print(f"**Question:** {label}\n✅ **Answer (Pre-filled):** {current_value}\n")
#                     continue
#
#                 new_answer = generate_answer(label)
#                 try:
#                     # field.fill(new_answer)
#                     field.fill(new_answer, force=True)
#
#                     print(f"**Question:** {label}\n📝 **Ollama Answer:** {new_answer}\n")
#                 except Exception as e:
#                     print(f"⚠️ Could not fill field '{label}': {e}")
#
#         # Navigate through steps
#         next_button = page.locator("button:has-text('Next')")
#         review_button = page.locator("button:has-text('Review')")
#         submit_button = page.locator("button:has-text('Submit')")
#
#         if submit_button.count() > 0 and submit_button.first.is_visible():
#             print("\n🚀 **Final Step: Clicking Submit...**\n")
#             submit_button.first.click()
#             return True
#
#         elif review_button.count() > 0 and review_button.first.is_visible():
#             print("\n🔎 **Reviewing before submission...**\n")
#             review_button.first.click()
#             time.sleep(3)
#
#         elif next_button.count() > 0 and next_button.first.is_visible():
#             print("\n✅ **Moving to the next step...**\n")
#             next_button.first.click()
#             time.sleep(3)
#
#         else:
#             print("\n✅ **All steps completed!**\n")
#             break
#
#     return False


def handle_easy_apply(page):
    max_steps = 10  # failsafe to prevent infinite loops
    steps = 0

    while steps < max_steps:
        # 🧠 Fill fields
        input_fields = page.locator("input, textarea")
        for i in range(input_fields.count()):
            field = input_fields.nth(i)
            label = field.get_attribute("aria-label")

            if label and field.is_enabled():
                current_value = field.input_value().strip()
                if current_value:
                    print(f"**Question:** {label}\n✅ **Answer (Pre-filled):** {current_value}\n")
                    continue
                try:
                    answer = generate_answer(label)
                    field.fill(answer)
                    print(f"**Question:** {label}\n🧠 **Answer (AI):** {answer}\n")
                except Exception as e:
                    print(f"⚠️ Error filling {label}: {e}")

        # 🔘 Check for navigation buttons
        if page.locator("button:has-text('Submit')").is_visible():
            page.locator("button:has-text('Submit')").click()
            print("🚀 Submitted application!")
            return True
        elif page.locator("button:has-text('Next')").is_visible():
            page.locator("button:has-text('Next')").click()
        elif page.locator("button:has-text('Review')").is_visible():
            page.locator("button:has-text('Review')").click()
        else:
            print("❌ No more steps or buttons.")
            break

        steps += 1
        time.sleep(2)

    return False

# Main function to apply for jobs
def apply_linkedin_jobs():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("🔐 Logging into LinkedIn...")
        page.goto("https://www.linkedin.com/login")
        page.fill("#username", email)
        page.fill("#password", password)
        page.click("button[type='submit']")
        page.wait_for_url("https://www.linkedin.com/feed/")
        print("✅ Login successful!")

        # Job search URL
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={job_title.replace(' ', '%20')}&location={location.replace(' ', '%20')}&f_AL=true"
        page.goto(search_url)
        page.wait_for_selector(".job-card-container--clickable")

        job_cards = page.locator(".job-card-container--clickable")
        total_jobs = job_cards.count()
        print(f"🔍 Found {total_jobs} jobs. Filtering only 'Easy Apply' jobs...")

        easy_apply_found = False

        for i in range(total_jobs):
            print(f"\n🎯 Checking job {i + 1} of {total_jobs}...")
            job_cards.nth(i).click()
            time.sleep(5)

            # Fetch company and role
            try:
                company = page.locator("a.topcard__org-name-link, span.topcard__flavor").first.inner_text().strip()
            except:
                company = "Unknown Company"

            try:
                role = page.locator("h1.topcard__title").first.inner_text().strip()
            except:
                role = job_title

            if already_applied(company, role):
                print(f"⏩ Already applied to: {company} - {role}. Skipping.")
                continue

            easy_apply_button = page.locator("button.jobs-apply-button:has-text('Easy Apply')").first
            if easy_apply_button.count() > 0 and easy_apply_button.is_visible():
                print("✅ Found 'Easy Apply' button. Clicking to open application form...")
                easy_apply_button.click()
                time.sleep(5)

                applied = handle_easy_apply(page)
                if applied:
                    print("📩 Application submitted!")
                    save_applied_job(company, role)
                    print(f"✅ Saved to CSV: {company} - {role}")
                easy_apply_found = True
                break
            else:
                print("❌ No Easy Apply button found. Moving to next job...")

        if not easy_apply_found:
            print("\n❌ No 'Easy Apply' jobs found.\n")

        print("\n🎯 **Job application process completed!**\n")
        browser.close()

# Run it
apply_linkedin_jobs()
