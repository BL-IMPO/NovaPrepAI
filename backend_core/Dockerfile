FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/* \

RUN apt-get update && apt-get install -y netcat-openbsd
# Install Firefox and geckodriver

RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    && wget https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz \
    && tar -xzf geckodriver-v0.34.0-linux64.tar.gz -C /usr/local/bin/ \
    && rm geckodriver-v0.34.0-linux64.tar.gz \
    && chmod +x /usr/local/bin/geckodriver

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]