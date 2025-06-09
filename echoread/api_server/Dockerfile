# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
# For now, we'll assume a requirements.txt might be added later
# RUN pip install --no-cache-dir -r requirements.txt
# Install FastAPI and Uvicorn
RUN pip install fastapi uvicorn psycopg2-binary sqlalchemy

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV MODULE_NAME="main"
ENV VARIABLE_NAME="app"

# Run main.py when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
