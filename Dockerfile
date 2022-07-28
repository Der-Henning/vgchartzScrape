FROM python:3.9-slim

RUN mkdir -p /app
RUN mkdir -p /csv
ENV CSV_PATH=/csv
VOLUME /csv
WORKDIR /app

COPY requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp

COPY ./vgchartzfull.py ./vgchartzfull.py

CMD [ "python", "./vgchartzfull.py" ]