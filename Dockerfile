FROM python:3.7.3
COPY . /app
COPY requirements.txt .
RUN apt-get -y update
RUN apt-get install -y ffmpeg
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN gdown --fuzzy https://drive.google.com/file/d/1mutYMUjqHhpv8P5Ca48Jd0a4tr3phHYn/view?usp=sharing
WORKDIR /app/kospeech/data
RUN gdown https://drive.google.com/drive/folders/1I8aS20Jm24v6yABIySip2REhOM_QgzUr?usp=sharing --folder
WORKDIR /app
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
