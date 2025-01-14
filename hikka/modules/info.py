from .. import loader, utils, version
import git
import platform
import psutil
import time
import os
from telethon.tl.types import MessageEntityUrl
import re


# ------------------------------------------------------- #

# meta developer: @kmodules
__version__ = (1, 0, 0)

# ------------------------------------------------------- #

@loader.tds
class KInfoMod(loader.Module):
    """Инфо для Hikka"""

    strings = {
        "name": "KInfo", 
        "update_available": "<b>Доступно обновление!</b>",
        "latest_version": "<b>У вас последняя версия.</b>",
    }

    async def client_ready(self, client, db):
        self.client = client
        self.db = db

    def __init__(self):
        self.config = loader.ModuleConfig(
            "custom_info_text",
            "<emoji document_id=5199889902807833553>🕸</emoji><emoji document_id=5199573827574588449>👍</emoji><emoji document_id=5199842529318561842>👍</emoji><emoji document_id=5199585003079493668>😭</emoji>\n"
            "<emoji document_id=5879770735999717115>👤</emoji>user: {owner}\n"
            "<emoji document_id=5877410604225924969>🔄</emoji>version: {version}\n"
            "<emoji document_id=5935989710420709120>🍎</emoji>branch: {branch}\n"
            "<emoji document_id=5994544674604322765>🤖</emoji>ping: {ping}\n"
            "<emoji document_id=5776213190387961618>🕓</emoji>uptime: {uptime}\n"
            "<emoji document_id=5879813604068298387>❗️</emoji>prefix: {prefix}",
            "{system_info}",
            """Шаблон для вывода информации
            
            {owner} - Вы,
            {version} - Версия юзербота,
            {update_status} - Статус версии,        
            {uptime} - Аптайм,
            {branch} - Ветка,
            {ping} - Пинг юзербота
            {prefix} - Префикс. 
            """,
            
            "banner_url",
            "https://0x0.st/s/ZOADD3_N_FlRRVn8-1uw9g/8-kB.png",
            "URL, который будет отправлен с информацией (None чтобы отключить)"
        )

    def get_cpu_info(self):
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":")[1].strip()
        except:
            return platform.processor() or "Unknown"

    def get_ram_info(self):
        try:
            ram = psutil.virtual_memory()
            total = round(ram.total / (1024**3), 2)
            used = round(ram.used / (1024**3), 2)
            return used, total
        except:
            return 0, 0

    def get_disk_info(self):
        try:
            disk = psutil.disk_usage('/')
            total = round(disk.total / (1024**3), 2)
            used = round(disk.used / (1024**3), 2)
            return used, total
        except:
            return 0, 0
            
    @loader.command()
    async def info(self, message):
        """Показать информацию о юзерботе"""
        try:
            repo = git.Repo(search_parent_directories=True)
            diff = repo.git.log([f"HEAD..origin/{version.branch}", "--oneline"])
            update_status = self.strings["update_available"] if diff else self.strings["latest_version"]
        except:
            update_status = "Невозможно проверить обновления"
            
        start = time.perf_counter_ns()
        msg = await message.client.send_message(message.peer_id, '⏳')
        ping = round((time.perf_counter_ns() - start) / 10**6, 3)
        await msg.delete()

        platform_name = utils.get_platform_name()
        is_termux = "Termux" in platform_name
        
        if is_termux:
            system_info = ""
        else:
            ram_used, ram_total = self.get_ram_info()
            disk_used, disk_total = self.get_disk_info()
            system_info = (
                f"<emoji document_id=5873146865637133757>🎤</emoji> <b>RAM сервера:</b> <code>{ram_used} GB | {ram_total} GB</code>\n"
                f"<emoji document_id=5870982283724328568>⚙</emoji> <b>Память:</b> <code>{disk_used} GB | {disk_total} GB</code>\n\n"
                f"<emoji document_id=5391034312759980875>🥷</emoji><b> OC: {platform.system()} {platform.release()}</b>\n"
                f"<emoji document_id=5235588635885054955>🎲</emoji> <b>Процессор:</b> <b>{self.get_cpu_info()}</b>"
            )

        info = self.config["custom_info_text"].format(
            owner=self._client.hikka_me.first_name + ' ' + (self._client.hikka_me.last_name or ''),
            version='.'.join(map(str, list(version.__version__))),
            branch=version.branch,
            update_status=update_status,
            prefix=self.get_prefix(),
            ping=ping,
            uptime=utils.formatted_uptime(),
            system_info=system_info
        )

        if self.config["banner_url"]:
            await self.client.send_file(
                message.peer_id,
                self.config["banner_url"],
                caption=info
            )
            if message.out:
                await message.delete()
        else:
            await utils.answer(message, info)

    @loader.command()
    async def setinfo(self, message):
        """Установить кастомный текст информации: .setcinfo <текст>"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<emoji document_id=5314413943035278948>🧠</emoji><b> Укажите текст для кастомной информации!")
            return

        self.config["custom_info_text"] = args
        await utils.answer(message, "<emoji document_id=5314413943035278948>🧠</emoji><b> K:CustomInfo - текст поставлен.</b>")
           
