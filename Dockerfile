# ---- Stage 1: Build Dependencies ----
# Use an official Python slim image as a base.
FROM python:3.11-slim AS builder

# Set the working directory for this stage.
WORKDIR /usr/src/app

# Copy the requirements file into the builder stage.
COPY requirements.txt ./

# Use pip wheel to pre-compile dependencies. This creates a cache of wheel files.
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt


# ---- Stage 2: Final Production Image ----
# Use the same slim Python image for a small final container size.
FROM python:3.11-slim

# Set the working directory inside the final container.
WORKDIR /usr/src/app

# Set non-root user for security
RUN useradd -m dockeradmin
USER dockeradmin

# Copy the pre-built wheel files from the builder stage.
COPY --from=builder /usr/src/app/wheels /wheels

# Copy the requirements.txt file again.
COPY --from=builder /usr/src/app/requirements.txt .

# Install the packages from the local wheel files.
# This is much faster than downloading from the internet again.
RUN pip install --no-cache /wheels/*

# Copy your application code into the final container.
COPY ./app ./app

# ADD THIS LINE: Copy your run script into the final container.
COPY run.py ./

# Set environment variables for Python.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Expose the port that the application will run on.
EXPOSE 8000

# CHANGE THIS LINE: Set the command to run your application using run.py
CMD ["python", "run.py"]
