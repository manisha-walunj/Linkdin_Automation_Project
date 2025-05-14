import os
import time
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright
from django.shortcuts import render
from .models import AppliedJob
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
email = os.getenv("LINKEDIN_EMAIL")
password = os.getenv("LINKEDIN_PASSWORD")

job_title = "Python Developer"
job_location = "Pune"


from django.http import HttpResponse

def home(request):
    return HttpResponse("<h1>Welcome to LinkedIn Job Auto Apply</h1><p>Go to <a href='/jobs/apply/'>Apply Jobs</a></p>")




# Function to check if the job is already applied
from django.http import HttpResponse
from asgiref.sync import sync_to_async
from .models import AppliedJob

async def is_already_applied(job_url):
    return await sync_to_async(AppliedJob.objects.filter(job_url=job_url).exists)()

async def apply_linkedin_job(request):
    job_url = "https://www.linkedin.com/jobs/search/?currentJobId=4194286497&f_AL=true&keywords=Python%20Developer&location=Pune"

    already_applied = await is_already_applied(job_url)
    if already_applied:
        return HttpResponse("Already applied!")

    await sync_to_async(AppliedJob.objects.create)(job_title="Python Developer", company_name="Unknown", job_url=job_url)

    return HttpResponse("Applied Successfully!")



# Function to save applied job in the database
def log_application(job_title, company_name, job_url):
    AppliedJob.objects.create(job_title=job_title, company_name=company_name, job_url=job_url)


# Ollama API function to fetch job-related information
def generate_with_ollama(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {"model": "llama2", "prompt": prompt, "stream": False}
    response = requests.post(url, json=payload)
    return response.json().get("response", "")


# Function to fill job application form
def fill_application_form(page):
    input_fields = page.locator("input, textarea").all()
    user_data = {
        "phone": "+91 98765-43210",
        "location": "Pune, Maharashtra, India",
        "email": "amit.sharma@example.com",
        "company": "Tech Innovations Pvt Ltd",
        "job_title": "Python Developer",
        "experience": "Worked on Django and Flask web apps",
        "skills": "Python, Django, Flask, SQL",
    }

    for field in input_fields:
        if not field.is_editable():
            continue

        label = field.evaluate("el => el.labels?.[0]?.textContent") or field.get_attribute("placeholder") or "unknown"
        label = label.strip().lower()

        if "phone" in label:
            field.fill(user_data["phone"])
        elif "location" in label:
            field.fill(user_data["location"])
        elif "experience" in label:
            field.fill(user_data["experience"])
        elif "skills" in label:
            field.fill(user_data["skills"])
        else:
            prompt = f"Provide a professional response for: {label} (Max 10 words)."
            value = generate_with_ollama(prompt)[:50]
            field.fill(value)




# Main function to apply for jobs
def apply_linkedin_job(request):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # LinkedIn login
        page.goto("https://www.linkedin.com/login")
        page.fill("#username", email)
        page.fill("#password", password)
        page.click("button[type='submit']")
        page.wait_for_url("https://www.linkedin.com/feed/")

        search_url = f"https://www.linkedin.com/jobs/search/?keywords={job_title.replace(' ', '%20')}&location={job_location.replace(' ', '%20')}&f_AL=true"
        page.goto(search_url)
        page.wait_for_selector(".job-card-container--clickable")

        job_cards = page.locator(".job-card-container--clickable")
        total_jobs = job_cards.count()

        for i in range(total_jobs):
            job = job_cards.nth(i)
            job.click()
            time.sleep(5)

            job_title_text = page.locator(".job-details-jobs-unified-top-card__job-title").text_content().strip()
            company_name = page.locator(".job-details-jobs-unified-top-card__company-name").text_content().strip()
            job_url = page.url

            if is_already_applied(job_url):
                continue

            apply_button = page.locator("button.jobs-apply-button").first
            if apply_button.is_visible():
                apply_button.click()
                fill_application_form(page)

                while True:
                    submit_button = page.locator("button:has-text('Submit')")
                    next_buttons = page.locator("button:has-text('Next')")
                    review_button = page.locator("button:has-text('Review')")

                    if review_button.is_visible():
                        review_button.click()
                        time.sleep(3)
                    elif submit_button.is_visible():
                        submit_button.click()
                        log_application(job_title_text, company_name, job_url)
                        break
                    elif next_buttons.count() > 0:
                        next_buttons.first.click()
                        time.sleep(3)
                    else:
                        break

        browser.close()



    return render(request, 'jobapply/job_status.html', {"message": "Job applications processed!"})
