FROM python:3.8-slim-buster as main
ADD . /
ENV Docker=true
RUN pip install -r requirements.txt
RUN apt update && apt install git -y
EXPOSE 8080
RUN mkdir /data
CMD ["python3", "-m", "hikka"]