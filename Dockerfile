FROM python:3.7-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*

#    && pip install cryptography \
#    && apt-get purge -y --auto-remove gcc and-build-dependencies

ADD ./setup.sh setup.sh
RUN ./setup.sh

# Add this entire directory into one called src/
ADD . /src

# Set working directory
WORKDIR /src

# Expose
EXPOSE 5001

CMD ["python3", "app.py"]
