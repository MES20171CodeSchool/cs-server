FROM debian:8.7

RUN apt-get update -
RUN apt-get install curl -y \
    python3.4\
    python3-pip \
    redis-server \
    build-essential

ADD ./ src
WORKDIR /src

RUN pip3 install --upgrade pip
RUN pip3 install awscli --upgrade --user
RUN pip3 install -r requirements-deploy.txt

ENV WSGI_APPLICATION=codeschool.wsgi \
    MEDIA_FOLDER=/var/www/media \
    CODESCHOOL_PRODUCTION=true
VOLUME ["/app/db/", "/var/www/media/", "/sock/"]

 # CMD python3 manage.py runserver
