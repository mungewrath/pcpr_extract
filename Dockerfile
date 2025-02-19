FROM python:3.6-slim

ADD ./setup.sh setup.sh
RUN ./setup.sh

# Add this entire directory into one called src/
ADD . /src

# Set working directory
WORKDIR /src

# Expose
EXPOSE 5001

CMD ["python3", "app.py"]
