FROM python:3.8
ADD . /
ENV OKTETO=true
RUN pip install -r requirements.txt
EXPOSE 8080
RUN mkdir /data
CMD ["python3", "-m", "hikka"]