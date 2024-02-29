# Use an official Python runtime as a parent image
FROM python:3.12.1-slim

# Set the working directory in the container
WORKDIR /code

# Copy the current directory contents into the container
COPY . .

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 for Flask application
EXPOSE 8080

# Run main.py when the container launches
CMD ["python", "main.py"]
