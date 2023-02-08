FROM python:3.8-slim-buster
ADD . /app
WORKDIR /app
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt
CMD ["python3", "app.py"]