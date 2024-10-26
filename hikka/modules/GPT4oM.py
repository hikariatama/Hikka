# meta developer: @htmIpage

import requests
import io
import os
from .. import loader, utils

class GPT4oMMod(loader.Module):
    """Based on docs.onlysq.com"""
    strings = {"name": "GPT4oM"}

    async def client_ready(self, client, db):
        self.client = client

    async def gptcmd(self, message):
        """Спросить нейросеть (GPT-4o mini)"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>Укажите вопрос!</b>")
            return

        await utils.answer(message, "<b>Спрашиваю GPT-4o mini...</b>")
        
        payload = {
            "model": "gpt-4o-mini",
            "request": {
                "messages": [
                    {
                        "role": "user",
                        "content": args
                    }
                ]
            }
        }

        try:
            response = requests.post('http://api.onlysq.ru/ai/v2', json=payload)
            response.raise_for_status()
            data = response.json()
            answer = data.get("answer", "Ответ не получен.")
            await utils.answer(message, f"<b>Запрос:</b>\n<code>{args}</code>\n\n<b>Ответ:</b>\n<code>{answer}</code>")

        except requests.exceptions.RequestException as e:
            await utils.answer(message, f"<b>Произошла ошибка при запросе:</b>\n<code>{str(e)}</code>")
    
    async def imgcmd(self, message):
        """Сгенерировать изображение (Kandinsky)"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>Укажите описание изображения!</b>")
            return

        await utils.answer(message, "<b>Генерирую изображение...</b>")
        
        payload = {
            "model": "kandinsky",
            "request": {
                "messages": [
                    {
                        "role": "user",
                        "content": args
                    }
                ],
                "meta": {
                    "image_count": 1
                }
            }
        }

        try:
            response = requests.post('http://api.onlysq.ru/ai/v2', json=payload)
            response.raise_for_status()
            data = response.json()
            images = data.get("answer", [])

            if images:
                for image_url in images:
                    try:
                        img_response = requests.get(image_url, stream=True)
                        img_response.raise_for_status()
                        
                        img_data = io.BytesIO(img_response.content)
                        img_data.name = 'generated_image.png'

                        await self.client.send_file(message.chat_id, img_data, caption=f"<b>Сгенерированное изображение по запросу:</b>\n<code>{args}</code>")
                    
                    except requests.exceptions.RequestException as img_error:
                        await utils.answer(message, f"<b>Ошибка при загрузке изображения:</b>\n<code>{str(img_error)}</code>")

            else:
                await utils.answer(message, "<b>Изображения не были сгенерированы.</b>")

        except requests.exceptions.RequestException as e:
            await utils.answer(message, f"<b>Произошла ошибка при генерации изображения:</b>\n<code>{str(e)}</code>")
