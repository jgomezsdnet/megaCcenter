FROM waltergomezb/gatewayapi-base
MAINTAINER WALTER GOMEZ

RUN apt-get update && \
    apt-get install -qy python-dev

ADD src/requirements.txt /
# Activate virtual environment and install wheel support
RUN . /appenv/bin/activate && \
    pip install -r requirements.txt



# Add test entrypoint script
COPY scripts/stage.sh /usr/local/bin/stage.sh
RUN chmod +x /usr/local/bin/stage.sh

# Set defaults for entrypoint and command string
ENTRYPOINT ["stage.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

EXPOSE 8000
# Add application source
COPY src /application
WORKDIR /application