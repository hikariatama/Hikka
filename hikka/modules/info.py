
import git
from hikkatl.tl.types import Message
from hikkatl.utils import get_display_name

from .. import loader, utils, version
from ..inline.types import InlineQuery
import time


@loader.tds
class HyekoInfoMod(loader.Module):
    """Show userbot info"""

    strings = {
        "name": "HikkaInfo",
        "_cfg_cst_msg": "Custom message",
        "_cfg_cst_btn": "Custom button",
        "_cfg_banner": "Custom banner",
        "update_required": "<b>Update required!</b>",
        "up-to-date": "<b>Up-to-date</b>",
        "owner": "Owner",
        "version": "Version",
        "branch": "Branch",
        "prefix": "Prefix",
        "uptime": "Uptime",
        "cpu_usage": "CPU",
        "ram_usage": "RAM",
        "send_info": "Send info",
        "description": "Shows bot info",
        "desc": "Show help",
        "setinfo_no_args": "No message",
        "setinfo_success": "Message set",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "custom_message",
                "<emoji document_id=5879770735999717115>👤</emoji>owner: {me}\n"
                "<emoji document_id=5877260593903177342>⚙️</emoji>version: {version}\n"
                "<emoji document_id=5879841310902324730>✏️</emoji>prefix: {prefix}\n"
                "<emoji document_id=5967816500415827773>💻</emoji>platform: {platform}\n"
                "<emoji document_id=5775981206319402773>🎞</emoji>uptime: {uptime}\n"
                "<emoji document_id=5931588842116091655>🗻</emoji>RAM: {ram_usage}\n"
                 "<emoji document_id=5936130851635990622>⚡️</emoji>ping: {ping}",
                lambda: self.strings("_cfg_cst_msg"),
            ),
            loader.ConfigValue(
                "banner_url",
                "https://0x0.st/s/ZOADD3_N_FlRRVn8-1uw9g/8-kB.png",
                lambda: self.strings("_cfg_banner"),
                validator=loader.validators.Link(),
            ),
        )

    def _render_info(self, inline: bool) -> str:
        try:
            repo = git.Repo(search_parent_directories=True)
            diff = repo.git.log([f"HEAD..origin/{version.branch}", "--oneline"])
            upd = self.strings("update_required") if diff else self.strings("up-to-date")
        except Exception:
            upd = ""
        
        start = time.perf_counter_ns()
        ping_msg =  utils.run_sync(self._client.send_message(self._client.hikka_me, '⏳'))
        ping = round((time.perf_counter_ns() - start) / 10**6, 3)
        utils.run_sync(ping_msg.delete())


        me = f'<b><a href="tg://user?id={self._client.hikka_me.id}">{utils.escape_html(get_display_name(self._client.hikka_me))}</a></b>'
        build = utils.get_commit_url()
        _version = f'<i>{".".join(map(str, version.__version__))}</i>'
        prefix = f"«<code>{utils.escape_html(self.get_prefix())}</code>»"
        platform = utils.get_named_platform()
        icons = {
            "🍊": "<emoji document_id=5449599833973203438>🧡</emoji>",
            "🍇": "<emoji document_id=5449468596952507859>💜</emoji>",
            "❓": "<emoji document_id=5407025283456835913>📱</emoji>",
            "🍀": "<emoji document_id=5395325195542078574>🍀</emoji>",
            "🦾": "<emoji document_id=5386766919154016047>🦾</emoji>",
            "🚂": "<emoji document_id=5359595190807962128>🚂</emoji>",
            "🐳": "<emoji document_id=5431815452437257407>🐳</emoji>",
            "🕶": "<emoji document_id=5407025283456835913>📱</emoji>",
            "🐈‍⬛": "<emoji document_id=6334750507294262724>🐈‍⬛</emoji>",
            "✌️": "<emoji document_id=5469986291380657759>✌️</emoji>",
            "📻": "<emoji document_id=5471952986970267163>💎</emoji>",
        }
        for emoji, icon in icons.items():
            platform = platform.replace(emoji, icon)

        if self.config["custom_message"]:
            msg = ("<b></b>\n" if "hikka" not in self.config["custom_message"].lower() else "") + self.config["custom_message"].format(
                me=me,
                version=_version,
                build=build,
                prefix=prefix,
                platform=platform,
                upd=upd,
                uptime=utils.formatted_uptime(),
                cpu_usage=utils.get_cpu_usage(),
                ram_usage=f"{utils.get_ram_usage()} MB",
                branch=version.branch,
                ping=ping
            )
        else:
            parts = (
                (utils.get_platform_emoji() if self._client.hikka_me.premium and not inline else "🌘 Hyeko"),
                "<emoji document_id=5373141891321699086>😎</emoji>",
                "<emoji document_id=5469741319330996757>💫</emoji>",
                "<emoji document_id=5449918202718985124>🌳</emoji>",
                "<emoji document_id=5472111548572900003>⌨️</emoji>",
                "<emoji document_id=5451646226975955576>⌛️</emoji>",
                "<emoji document_id=5431449001532594346>⚡️</emoji>",
                "<emoji document_id=5359785904535774578>💼</emoji>",
                 platform,
            )
            msg = (
                 f'<b>{{}}</b>\n\n<b>{{}} {self.strings("owner")}:</b> {me}\n\n<b>{{}}'
                f' {self.strings("version")}:</b> {_version} {build}\n<b>{{}}'
                f' {self.strings("branch")}:</b> <code>{version.branch}</code>\n{upd}\n\n<b>{{}}'
                f' {self.strings("prefix")}:</b> {prefix}\n<b>{{}}'
                f' {self.strings("uptime")}:</b> {utils.formatted_uptime()}\n\n<b>{{}}'
                f' {self.strings("cpu_usage")}:</b> <i>~{utils.get_cpu_usage()} %</i>\n<b>{{}}'
                f' {self.strings("ram_usage")}:</b> <i>~{utils.get_ram_usage()} MB</i>\n<b>{{}}'
                f' {self.strings("ping")}:</b> <i>~{ping} ms</i>\n<b>{{}}</b>'
            ).format(*map(lambda x: utils.remove_html(x) if inline else x, parts))

        return msg

    def _get_mark(self):
        return (
            {"text": self.config["custom_button"][0], "url": self.config["custom_button"][1]}
            if self.config["custom_button"]
            else None
        )

    @loader.inline_handler(
        thumb_url="https://img.icons8.com/external-others-inmotus-design/344/external-Moon-round-icons-others-inmotus-design-2.png"
    )
    @loader.inline_everyone
    async def info(self, _: InlineQuery) -> dict:
        return {
            "title": self.strings("send_info"),
            "description": self.strings("description"),
            **({"photo": self.config["banner_url"], "caption": self._render_info(True)}
               if self.config["banner_url"] else {"message": self._render_info(True)}),
            "thumb": "https://github.com/hikariatama/Hikka/raw/master/assets/hikka_pfp.png",
            "reply_markup": self._get_mark(),
        }

    @loader.command()
    async def infocmd(self, message: Message):
        kwargs = {"photo": self.config["banner_url"]} if self.config["banner_url"] else {}
        await self.inline.form(
            message=message,
            text=self._render_info(True),
            reply_markup=self._get_mark(),
             **kwargs
        ) if self.config["custom_button"] else await utils.answer_file(
            message, self.config["banner_url"], self._render_info(False)
        )

    @loader.command()
    async def hyekoinfo(self, message: Message):
        await utils.answer(message, self.strings("desc"))

    @loader.command()
    async def setinfo(self, message: Message):
        if not (args := utils.get_args_html(message)):
            return await utils.answer(message, self.strings("setinfo_no_args"))

        self.config["custom_message"] = args
        await utils.answer(message, self.strings("setinfo_success"))
