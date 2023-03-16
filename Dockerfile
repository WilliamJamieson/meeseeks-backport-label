# Container image that runs your code
FROM python:3.11

# Copies code file action repository to the filesystem path `/` of the container
COPY requirements.txt /requirements.txt
COPY tools /tools
COPY entrypoint.sh /entrypoint.sh

RUN pip3 install -r /requirements.txt

# Code file to execute when the docker container starts up (`entrypoint.sh`)
ENTRYPOINT ["/entrypoint.sh"]
