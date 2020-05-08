FROM bitnami/minideb:buster

COPY requirements.txt .
RUN apt-get update -y \
    && apt-get install -y python3 python3-pip libpq-dev \
    && pip3 install -r requirements.txt --no-cache-dir \
    && apt-get remove -y python3-pip \
    && apt -y autoremove \
    && apt-get -y clean \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir /coral-vm-app
COPY *.py all_slides.db ./coral-vm-app/
RUN ls -l
RUN mkdir ./coral-vm-app/static
RUN mkdir ./coral-vm-app/templates
ADD static/ ./coral-vm-app/static
ADD templates/ ./coral-vm-app/templates

WORKDIR ./coral-vm-app/
CMD ["python3", "app.py", "-p", "80", "-l", "0.0.0.0"]
