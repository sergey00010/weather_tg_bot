FROM python:3.9-slim

ENV TZ=Europe/Moscow
RUN apt-get update && apt-get install -y tzdata
RUN dpkg-reconfigure -f noninteractive tzdata


WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
ENV PYTHONUNBUFFERED 1
CMD ["python", "weather.py"]
