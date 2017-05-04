FROM debian:8.7

RUN apt-get update -
RUN apt-get install curl -y \
    python3.4\
    python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install awscli --upgrade --user

RUN pip3 install \
            gunicorn \
            lazyutils \
            Markdown \
            PyYAML \
            fake-factory \
            factory-boy \
            mommys_boy \
            pygments \
            html5lib \
            bleach \
            pygeneric \
            srvice \
            jinja2

# E-judge support
RUN pip3 install \
            markio \
            iospec \
            ejudge \
            boxed

# Django deps
RUN pip3 install \
            django==1.10 \
            wagtail==1.9 \
            wagtail-model-tools \
            django-model-utils \
            django-picklefield \
            django-jsonfield \
            django-annoying \
            django-compressor \
            django-userena \
            django-polymorphic \
            django-guardian>=1.4.6 \
            django-model-reference

# Extra dependencies for additional language support
#RUN pip3 install \
#            pytuga
WORKDIR /app/src
COPY $PWD  /app/src
ENV WSGI_APPLICATION=codeschool.wsgi \
    MEDIA_FOLDER=/var/www/media \
    CODESCHOOL_PRODUCTION=true
VOLUME ["/app/db/", "/var/www/media/", "/sock/"]

CMD python3 manage.py runserver
