FROM python:3.8.2-slim-buster

RUN apt-get update -y; apt-get upgrade -y; apt-get install -y default-libmysqlclient-dev python-dev gcc

ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY ./build/acquire/requirements.txt ./

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

ENV PYTHON_ENV="production"

# copy repo
WORKDIR /app
COPY . .
