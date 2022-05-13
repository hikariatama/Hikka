FROM python:3.8-slim-buster as main
ADD . /
ENV Docker=true
RUN pip install -r requirements.txt
EXPOSE 3902
RUN mkdir /data
CMD ["python3", "-m", "hikka"]