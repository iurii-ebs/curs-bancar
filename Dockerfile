FROM python:3.8

# Install missing libs
RUN apt-get update && apt-get install -y apt-transport-https
RUN apt-get install -y curl wget git

# Creating Application Source Code Directory
RUN mkdir -p /usr/app

# Setting Home Directory for containers
WORKDIR /usr/app

# Installing python dependencies
COPY . /usr/app
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Collect static files
RUN python manage.py collectstatic --noinput

# Exposing Ports
EXPOSE 5432 8000 8014 8015 8016 8017
