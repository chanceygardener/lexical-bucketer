FROM python:3.9

WORKDIR /app

ARG SPACY_MODEL

ENV SPACY_MODEL=${SPACY_MODEL}

COPY requirements.txt .

# Copy the buckets into the image
COPY buckets ./buckets

RUN python -m pip install --upgrade pip

#RUN pip install websocket

#RUN pip install websocket-client

RUN python -m pip install lemminflect

RUN pip install --default-timeout=100  -r requirements.txt

# Install spacy model
#RUN python -m spacy download $SPACY_MODEL

COPY base_choice.py .

COPY server.py .

COPY parse_rules.py .

COPY utils.py .

#COPY blenderbot.py .

COPY .env .

EXPOSE 8080

CMD ["waitress-serve", "server:app"]
