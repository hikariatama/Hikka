#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import re
import string

from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.functions.contacts import UnblockRequest
from telethon.tl.types import Message

from .. import loader, utils
from ..inline.types import BotInlineMessage


@loader.tds
class InlineStuffMod(loader.Module):
    """Provides support for inline stuff"""

    strings = {
        "name": "InlineStuff",
        "bot_username_invalid": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Specified bot"
            " username is invalid. It must end with </b><code>bot</code><b> and contain"
            " at least 4 symbols</b>"
        ),
        "bot_username_occupied": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>This username is"
            " already occupied</b>"
        ),
        "bot_updated": (
            "<emoji document_id=6318792204118656433>🎉</emoji> <b>Config successfully"
            " saved. Restart userbot to apply changes</b>"
        ),
        "this_is_hikka": (
            "🌘 <b>Hi! This is Hikka — powerful modular Telegram userbot. You can"
            " install it to your account!</b>\n\n<b>🌍 <a"
            ' href="https://github.com/hikaraitama/Hikka">GitHub</a></b>\n<b>👥 <a'
            ' href="https://t.me/hikka_talks">Support chat</a></b>'
        ),
    }

    strings_ru = {
        "bot_username_invalid": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Неправильный ник"
            " бота. Он должен заканчиваться на </b><code>bot</code><b> и быть не короче"
            " чем 5 символов</b>"
        ),
        "bot_username_occupied": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Такой ник бота уже"
            " занят</b>"
        ),
        "bot_updated": (
            "<emoji document_id=6318792204118656433>🎉</emoji> <b>Настройки сохранены."
            " Для их применения нужно перезагрузить юзербот</b>"
        ),
        "this_is_hikka": (
            "🌘 <b>Привет! Это Hikka — мощный модульный Telegram юзербот. Вы можете"
            " установить его на свой аккаунт!</b>\n\n<b>🌍 <a"
            ' href="https://github.com/hikariaitama/Hikka">GitHub</a></b>\n<b>👥 <a'
            ' href="https://t.me/hikka_talks">Чат поддержки</a></b>'
        ),
    }

    strings_de = {
        "bot_username_invalid": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Der angegebene"
            " Benutzername ist ungültig. Er muss mit </b><code>bot</code><b> enden und"
            " mindestens 4 Zeichen lang sein</b>"
        ),
        "bot_username_occupied": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Dieser Benutzername"
            " ist bereits vergeben</b>"
        ),
        "bot_updated": (
            "<emoji document_id=6318792204118656433>🎉</emoji> <b>Erfolgreich"
            " gespeichert. Starte den Userbot neu, um die Änderungen zu übernehmen</b>"
        ),
        "this_is_hikka": (
            "🌘 <b>Hallo! Das ist Hikka — mächtiger modulare Telegram Userbot. Du kannst"
            " ihn auf deinen Account installieren!</b>\n\n<b>🌍 <a"
            ' href="https://github.com/hikariaitama/Hikka">GitHub</a></b>\n<b>👥 <a'
            ' href="https://t.me/hikka_talks">Support Chat</a></b>'
        ),
    }

    strings_tr = {
        "bot_username_invalid": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Belirtilen bot"
            " kullanıcı adı geçersiz. Botun adı </b><code>bot</code><b> ile bitmeli ve"
            " en az 4 karakter içermelidir</b>"
        ),
        "bot_username_occupied": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Bu kullanıcı adı"
            " zaten alınmış</b>"
        ),
        "bot_updated": (
            "<emoji document_id=6318792204118656433>🎉</emoji> <b>Yapılandırma başarıyla"
            " kaydedildi. Değişiklikleri uygulamak için botu yeniden başlatın</b>"
        ),
        "this_is_hikka": (
            "🌘 <b>Merhaba! Bu Hikka — güçlü modüler Telegram kullanıcı botu. Hesabınıza"
            " kurup, kullanabilirsiniz!</b>\n\n<b>🌍 <a"
            ' href="https://github.com/hikariaitama/Hikka">GitHub</a></b>\n<b>👥 <a'
            ' href="https://t.me/hikka_talks">Destek sohbeti</a></b>'
        ),
    }

    strings_hi = {
        "bot_username_invalid": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>बॉट उपयोगकर्ता"
            " नाम अवैध है। यह </b><code>bot</code><b> से समाप्त होना चाहिए और न्यूनतम"
            " 4 वर्णों का होना चाहिए</b>"
        ),
        "bot_username_occupied": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>यह उपयोगकर्ता नाम पहले"
            " से ही ले लिया गया है</b>"
        ),
        "bot_updated": (
            "<emoji document_id=6318792204118656433>🎉</emoji> <b>कॉन्फ़िगरेशन"
            " सफलतापूर्वक सहेजा गया। इसे लागू करने के लिए बॉट को रीस्टार्ट करें</b>"
        ),
        "this_is_hikka": (
            "🌘 <b>नमस्ते! यह Hikka है — एक मजबूत और मॉड्यूलर टेलीग्राम यूजरबॉट। आप इसे"
            " अपने अकाउंट पर इंस्टॉल कर सकते हैं!</b>\n\n<b>🌍 <a"
            ' href="https://github.com/hikariaitama/Hikka">GitHub</a></b>\n<b>👥 <a'
            ' href="https://t.me/hikka_talks">सपोर्ट चैट</a></b>'
        ),
    }

    strings_uz = {
        "bot_username_invalid": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Bot foydalanuvchi"
            " nomi noto'g'ri. U </b><code>bot</code><b> bilan tugashi kerak va kamida 4"
            " belgidan iborat bo'lishi kerak</b>"
        ),
        "bot_username_occupied": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Ushbu foydalanuvchi"
            " nomi allaqachon band</b>"
        ),
        "bot_updated": (
            "<emoji document_id=6318792204118656433>🎉</emoji> <b>Konfiguratsiya"
            " muvaffaqiyatli saqlandi. Ushbu o'zgarishlarni qo'llash uchun botni qayta"
            " ishga tushiring</b>"
        ),
        "this_is_hikka": (
            "🌘 <b>Salom! Bu Hikka - kuchli modulli Telegram userboti. Siz uni"
            " o'zingizni akkauntingizga o'rnatishingiz mumkin!</b>\n\n<b>🌍 <a"
            ' href="https://github.com/hikariaitama/Hikka">GitHub</a></b>\n<b>👥 <a'
            ' href="https://t.me/hikka_talks">Yordam chati</a></b>'
        ),
    }

    strings_jp = {
        "bot_username_invalid": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>ボットのユーザー名が"
            "無効です。それは</b><code>bot</code><b>で終わり、少なくとも4文字でなければなりません</b>"
        ),
        "bot_username_occupied": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>このユーザー名はすでに"
            "使用されています</b>"
        ),
        "bot_updated": (
            "<emoji document_id=6318792204118656433>🎉</emoji> <b>設定が正常に保存されました。"
            "変更を適用するには、ボットを再起動してください</b>"
        ),
        "this_is_hikka": (
            "🌘 <b>こんにちは！これはHikkaです — 力強いモジュール式のTelegramユーザーボットです。"
            "あなたはそれをあなたのアカウントにインストールすることができます！</b>\n\n<b>🌍 <a"
            ' href="https://github.com/hikariaitama/Hikka">GitHub</a></b>\n<b>👥 <a'
            ' href="https://t.me/hikka_talks">サポートチャット</a></b>'
        ),
    }

    strings_kr = {
        "bot_username_invalid": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>봇 사용자 이름이"
            " 잘못되었습니다. 그것은 </b><code>bot</code><b>으로 끝나야하며 최소 4자여야합니다</b>"
        ),
        "bot_username_occupied": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>이 사용자 이름은"
            " 이미 사용 중입니다</b>"
        ),
        "bot_updated": (
            "<emoji document_id=6318792204118656433>🎉</emoji> <b>설정이 성공적으로"
            " 저장되었습니다. 이러한 변경 사항을 적용하려면 봇을 다시 시작하십시오</b>"
        ),
        "this_is_hikka": (
            "🌘 <b>안녕하세요! 이것은 Hikka입니다 — 강력하고 모듈식인 Telegram 사용자 봇입니다."
            "당신은 그것을 당신의 계정에 설치할 수 있습니다!</b>\n\n<b>🌍 <a"
            ' href="https://github.com/hikariaitama/Hikka">GitHub</a></b>\n<b>👥 <a'
            ' href="https://t.me/hikka_talks">지원 채팅</a></b>'
        ),
    }

    strings_ar = {
        "bot_username_invalid": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>اسم مستخدم البوت"
            " غير صالح. يجب أن ينتهي بـ </b><code>bot</code><b> وأن يكون"
            " أكثر من 4 أحرف</b>"
        ),
        "bot_username_occupied": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>اسم المستخدم مأخوذ"
            " بالفعل</b>"
        ),
        "bot_updated": (
            "<emoji document_id=6318792204118656433>🎉</emoji> <b>تم حفظ الإعدادات"
            " بنجاح. يرجى إعادة تشغيل البوت لتطبيق التغييرات</b>"
        ),
        "this_is_hikka": (
            "🌘 <b>مرحبًا! هذا هو Hikka - مستخدم بوت تيليغرام قوي وموديولي. يمكنك تثبيته"
            " على حسابك!</b>\n\n<b>🌍 <a"
            ' href="https://github.com/hikariaitama/Hikka">GitHub</a></b>\n<b>👥 <a'
            ' href="https://t.me/hikka_talks">دردشة الدعم</a></b>'
        ),
    }

    strings_es = {
        "bot_username_invalid": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>El nombre de usuario"
            " del bot no es válido. Debe terminar con </b><code>bot</code><b> y"
            " tener al menos 4 caracteres</b>"
        ),
        "bot_username_occupied": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>El nombre de usuario"
            " ya está en uso</b>"
        ),
        "bot_updated": (
            "<emoji document_id=6318792204118656433>🎉</emoji> <b>La configuración se"
            " guardó correctamente. Reinicie el bot para aplicar los cambios</b>"
        ),
        "this_is_hikka": (
            "🌘 <b>¡Hola! Este es Hikka - un poderoso bot de usuario modular de"
            " Telegram. ¡Puedes instalarlo en tu cuenta!</b>\n\n<b>🌍 <a"
            ' href="https://github.com/hikariaitama/Hikka">GitHub</a></b>\n<b>👥 <a'
            ' href="https://t.me/hikka_talks">Chat de soporte</a></b>'
        ),
    }

    async def watcher(self, message: Message):
        if (
            getattr(message, "out", False)
            and getattr(message, "via_bot_id", False)
            and message.via_bot_id == self.inline.bot_id
            and "This message will be deleted automatically"
            in getattr(message, "raw_text", "")
        ):
            await message.delete()
            return

        if (
            not getattr(message, "out", False)
            or not getattr(message, "via_bot_id", False)
            or message.via_bot_id != self.inline.bot_id
            or "Opening gallery..." not in getattr(message, "raw_text", "")
        ):
            return

        id_ = re.search(r"#id: ([a-zA-Z0-9]+)", message.raw_text)[1]

        await message.delete()

        m = await message.respond("🌘")

        await self.inline.gallery(
            message=m,
            next_handler=self.inline._custom_map[id_]["handler"],
            caption=self.inline._custom_map[id_].get("caption", ""),
            force_me=self.inline._custom_map[id_].get("force_me", False),
            disable_security=self.inline._custom_map[id_].get(
                "disable_security", False
            ),
            silent=True,
        )

    async def _check_bot(self, username: str) -> bool:
        async with self._client.conversation("@BotFather", exclusive=False) as conv:
            try:
                m = await conv.send_message("/token")
            except YouBlockedUserError:
                await self._client(UnblockRequest(id="@BotFather"))
                m = await conv.send_message("/token")

            r = await conv.get_response()

            await m.delete()
            await r.delete()

            if not hasattr(r, "reply_markup") or not hasattr(r.reply_markup, "rows"):
                return False

            for row in r.reply_markup.rows:
                for button in row.buttons:
                    if username != button.text.strip("@"):
                        continue

                    m = await conv.send_message("/cancel")
                    r = await conv.get_response()

                    await m.delete()
                    await r.delete()

                    return True

    @loader.command(
        ru_doc="<юзернейм> - Изменить юзернейм инлайн бота",
        de_doc="<username> - Ändere den Inline-Bot-Nutzernamen",
        tr_doc="<kullanıcı adı> - İçe aktarma botunun kullanıcı adını değiştirin",
        hi_doc="<उपयोगकर्ता नाम> - इनलाइन बॉट का उपयोगकर्ता नाम बदलें",
        uz_doc="<foydalanuvchi nomi> - Bot foydalanuvchi nomini o'zgartiring",
        jp_doc="<ユーザー名> - インラインボットのユーザー名を変更します",
        kr_doc="<사용자 이름> - 인라인 봇의 사용자 이름을 변경합니다",
        ar_doc="<اسم المستخدم> - تغيير اسم المستخدم للبوت الداخلي",
        es_doc="<nombre de usuario> - Cambia el nombre de usuario del bot de inline",
    )
    async def ch_hikka_bot(self, message: Message):
        """<username> - Change your Hikka inline bot username"""
        args = utils.get_args_raw(message).strip("@")
        if (
            not args
            or not args.lower().endswith("bot")
            or len(args) <= 4
            or any(
                litera not in (string.ascii_letters + string.digits + "_")
                for litera in args
            )
        ):
            await utils.answer(message, self.strings("bot_username_invalid"))
            return

        try:
            await self._client.get_entity(f"@{args}")
        except ValueError:
            pass
        else:
            if not await self._check_bot(args):
                await utils.answer(message, self.strings("bot_username_occupied"))
                return

        self._db.set("hikka.inline", "custom_bot", args)
        self._db.set("hikka.inline", "bot_token", None)
        await utils.answer(message, self.strings("bot_updated"))

    async def aiogram_watcher(self, message: BotInlineMessage):
        if message.text != "/start":
            return

        await message.answer_photo(
            "https://github.com/hikariatama/assets/raw/master/hikka_banner.png",
            caption=self.strings("this_is_hikka"),
        )

    async def client_ready(self):
        if self.get("migrated"):
            return

        self.set("migrated", True)
        async with self._client.conversation("@BotFather") as conv:
            for msg in [
                "/cancel",
                "/setinline",
                f"@{self.inline.bot_username}",
                "user@hikka:~$",
            ]:
                m = await conv.send_message(msg)
                r = await conv.get_response()

                await m.delete()
                await r.delete()
