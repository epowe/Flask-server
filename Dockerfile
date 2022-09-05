FROM python:3.7.3
COPY . /app
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN TMPDIR=/mnt/d/tmp/ pip install -U -r requirements.txt
WORKDIR /app
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
