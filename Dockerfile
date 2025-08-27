FROM python:3.12.1-slim-buster
RUN mkdir /app && chmod 777 /app
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive
COPY . .
RUN apt -qq update && apt upgrade -y
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt
CMD [ "python3", "bot.py" ]