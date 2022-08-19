FROM python:3.7.3
COPY . /app
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt				
WORKDIR /app
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
