# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container to /code
WORKDIR /code 

# Copy the file with the requirements to the /code directory
COPY ./requirements.txt /code/requirements.txt

# Install the package dependencies in the requirements file
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

EXPOSE 10000

# Copy the ./app directory inside the /code directory
COPY . /code/app

# Set the command to run the uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]