FROM python:3.8-slim-buster

RUN apt-get update -y; apt-get upgrade -y; apt-get install -y default-libmysqlclient-dev python-dev gcc

ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY ./build/app/requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# streamlit-specific commands for config
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV PYTHON_ENV="production"

WORKDIR /app
COPY . .
EXPOSE 8501
