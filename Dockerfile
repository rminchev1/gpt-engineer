# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container to /app
WORKDIR /app

# Add current directory files to /app in container
COPY . /app

#RUN ls -al
RUN apt-get update \
 && apt-get install -y sudo tk tcl

#RUN apt-get install python3-tk 

RUN python -m pip install -e .

# Install any needed packages specified in requirements.txt

WORKDIR /app/fast-api
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 8000

#WORKDIR /app/fast-api

# Run main.py when the container launches
CMD ["python", "main.py"]
