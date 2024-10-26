
from .. import loader, utils  # pylint: disable=relative-beyond-top-level
import logging
from os import remove as DelFile
import requests
from requests import HTTPError



@loader.tds
class oxoMod(loader.Module):
    """0x0.st reuploader"""
    strings = {
        "name": "0x0.st Reuploader",
        "connection_error": "Host is unreachable for now, try again later.",
        "no_reply": "<b>You must be reply to a message with media</b>",
        "success": "URL for <code>{}</code>:\n\n<code>{}</code>",
        "error": "An error occured:\n<code>{}</code>",
        "uploading": "<b>Uploading {} ({}{})...</b>"
    }

    async def client_ready(self, client, db):
        self.client = client

    @loader.sudo
    async def zxzcmd(self, message):
        """Reupload to 0x0.st.слито тут - @mqone"""
        reply = await message.get_reply_message()
        if not reply or not reply.media:
            return await utils.answer(message, self.strings('no_reply',
                                                            message))
        size_len, size_unit = self.convert(reply.file.size)
        await utils.answer(message,
                           self.strings('uploading',
                                        message).format(reply.file.name,
                                                        size_len,
                                                        size_unit))
        path = await self.client.download_media(reply)
        try:
            uploaded = await upload(path)
        except ConnectionError:
            return await utils.answer(message,
                                      self.strings('connection_error',
                                                   message))
        except HTTPError as e:
            return await utils.answer(message,
                                      self.strings('error',
                                                   message).format(str(e)))
        return await utils.answer(message, self.strings('success',
                                  message).format(path, uploaded))

    def convert(self, size):
        power = 2**10
        zero = 0
        units = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
        while size > power:
            size /= power
            zero += 1
        return round(size, 2), units[zero]


async def upload(path):
    try:
        req = requests.post('https://0x0.st',
                            files={'file': open(path, 'rb')})
    except ConnectionError:
        DelFile(path)
        raise ConnectionError()
    if req.status_code != 200:
        DelFile(path)
        raise HTTPError(req.text)
    DelFile(path)
    return req.text
