FROM debian:latest

RUN apt update && apt install -y python3-pip


RUN useradd -m mzn-dispatcher
USER mzn-dispatcher

COPY requirements.txt .
ENV PATH="${PATH}:/home/mzn-dispatcher/.local/bin"
RUN pip install --user -r requirements.txt

COPY src src

CMD uvicorn --host 0.0.0.0 --port 8080 src.main:app
