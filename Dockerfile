# Ubuntu 20 with python3.8
FROM fnndsc/ubuntu-python3

WORKDIR /lazy-wifi
COPY ./lazy_wifi ./lazy_wifi
COPY requirements.txt .

# Update pip
RUN pip install -U pip

# Install packages
RUN pip install --quiet -r requirements.txt

# Install airmong-ng
RUN apt-get update
RUN apt-get install -y aircrack-ng

#Add env variable
ENV IN_DOCKER_ENV True
# Run
ENTRYPOINT ["python3", "-m", "lazy_wifi"]