FROM python:3.8
ADD . /
ENV OKTETO=true
RUN pip install -r requirements.txt
RUN pip install -r optional_requirements.txt
RUN apt update && apt install ffmpeg libavcodec-dev libavutil-dev libavformat-dev libswscale-dev libavdevice-dev -y
EXPOSE 8080
RUN mkdir /data
CMD ["python3", "-m", "hikka"]