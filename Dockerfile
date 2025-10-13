# FILE: Dockerfile (Corrected)

# 1. Start with a lean official Python image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /code

# 3. Create the 'data' directory AS THE ROOT USER (who has permission)
# The -p flag ensures it doesn't error if the directory already exists
RUN mkdir -p /code/data

# 4. Copy the requirements file and install dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 5. Copy the rest of your application code into the container
COPY ./ /code/

# 6. Change the ownership of the entire /code directory to a non-root user
# This gives your application permission to write to the 'data' sub-directory
RUN chown -R 1000:1000 /code

# 7. Switch to the non-root user for security
USER 1000

# 8. This command will be run when the container starts
CMD ["python", "run.py"]