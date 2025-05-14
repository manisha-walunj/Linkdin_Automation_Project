FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and dependencies
RUN pip install playwright && playwright install --with-deps

# Copy the entire app folder into the container
COPY . .

CMD ["python", "Linkdin_Automation.py"]
