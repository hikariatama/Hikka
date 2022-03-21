ENV TZ=Europe/Moscow

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && git clone https://github.com/hikariatama/Hikka.git /root/Hikka/ \
    && pip3 install --no-cache-dir -r root/Hikka/requirements.txt \
    && pip3 install av --no-binary av

WORKDIR /root/Hikka/

# start the bot
CMD ["python3", "-m", "hikka", "--root"]