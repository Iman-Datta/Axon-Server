# 1. Start with a lightweight Linux environment that has Python installed
FROM python:3.14.2-slim

# 2. Prevent Python from creating junk files and ensure logs print immediately
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Create a dedicated folder inside the container for your app
WORKDIR /app

# 4. Copy ONLY the requirements file first
COPY requirements.txt /app/

# 5. Install your Python dependencies inside the container
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 6. Copy the rest of your Axon-Server project files into the container
COPY . /app/

# 7. Document that this container uses port 8000
EXPOSE 8000

# 8. The command to run your server when the container starts
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]