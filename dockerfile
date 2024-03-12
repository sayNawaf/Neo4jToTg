# Use an official Python runtime as a parent image

FROM python:3.11.4-slim AS base

# Set the working directory to /app
WORKDIR /app

# Expose ports
EXPOSE 5000

# Copy the current directory contents into the container at /app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Define environment variable
ENV FLASK_APP=main.py

# Run flask when the container launches
# CMD ["python3", "main.py"]


CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]