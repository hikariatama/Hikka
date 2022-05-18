from .. import loader, utils
import siaskynet as skynet
import os

@loader.tds
class SkynetUploaderMod(loader.Module):
    """siasky.net uploader"""
    strings = {"name": "SkynetUploader"}

    async def skycmd(self, message):
        """ .sky <реплай на файл> - загружает файл на хост
        или
        .sky <реплай на текст> - загружает текст из реплая на хост
        """
        await message.edit("<b>🍃Загружаю...</b>")
        client = skynet.SkynetClient()
        reply = await message.get_reply_message()
        if not reply:
            await message.edit("Реплаем на файл!")
            return
        try:
            file = await reply.download_media()
            link = client.upload_file(file)
            filtered = link.split('sia://')
            link = f'https://siasky.net/{str(filtered[1])}'
            await message.edit("🌌Линк: \n" + link)
        except:
            with open('text.txt', 'w') as f:
                f.write(reply.raw_text)
            link = client.upload_file("text.txt")
            filtered = link.split('sia://')
            link = f'https://siasky.net/{str(filtered[1])}'
            await message.edit("🌌Линк: \n" + link)
            os.remove('text.txt')