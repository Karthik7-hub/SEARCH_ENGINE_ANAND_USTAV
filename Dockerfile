# FILE: Dockerfile

# Start with a modern, efficient Python version
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /code

# Copy the requirements file first to leverage Docker's caching
COPY ./requirements.txt /code/requirements.txt

# Install all your project's dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the rest of your application code (including the 'app' directory)
COPY ./ /code/

# This is the command that Hugging Face will run to start your API
CMD ["python", "run.py"]