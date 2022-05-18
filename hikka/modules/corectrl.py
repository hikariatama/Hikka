#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2021 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import os

from telethon.tl.types import Message

from .. import loader, main, translations, utils


@loader.tds
class CoreMod(loader.Module):
    """Control core userbot settings"""

    strings = {
        "name": "Settings",
        "too_many_args": "🚫 <b>Too many args</b>",
        "blacklisted": "✅ <b>Chat {} blacklisted from userbot</b>",
        "unblacklisted": "✅ <b>Chat {} unblacklisted from userbot</b>",
        "user_blacklisted": "✅ <b>User {} blacklisted from userbot</b>",
        "user_unblacklisted": "✅ <b>User {} unblacklisted from userbot</b>",
        "what_prefix": "❓ <b>What should the prefix be set to?</b>",
        "prefix_incorrect": "🚫 <b>Prefix must be one symbol in length</b>",
        "prefix_set": "✅ <b>Command prefix updated. Type</b> <code>{newprefix}setprefix {oldprefix}</code> <b>to change it back</b>",
        "alias_created": "✅ <b>Alias created. Access it with</b> <code>{}</code>",
        "aliases": "<b>Aliases:</b>\n",
        "no_command": "🚫 <b>Command</b> <code>{}</code> <b>does not exist</b>",
        "alias_args": "🚫 <b>You must provide a command and the alias for it</b>",
        "delalias_args": "🚫 <b>You must provide the alias name</b>",
        "alias_removed": "✅ <b>Alias</b> <code>{}</code> <b>removed.",
        "no_alias": "<b>🚫 Alias</b> <code>{}</code> <b>does not exist</b>",
        "db_cleared": "<b>✅ Database cleared</b>",
        "amore": "🌌 <b>Amore userbot</b>\n<b>Version: {}.{}.{}</b>",
        "check_url": "🚫 <b>You need to specify valid url containing a langpack</b>",
        "lang_saved": "{} <b>Language saved!</b>",
        "pack_saved": "✅ <b>Translate pack saved!</b>",
        "incorrect_language": "🚫 <b>Incorrect language specified</b>",
        "lang_removed": "✅ <b>Translations reset to default ones</b>",
        "check_pack": "🚫 <b>Invalid pack format in url</b>",
    }

    strings_ru = {
        "too_many_args": "🚫 <b>Слишком много аргументов</b>",
        "blacklisted": "✅ <b>Чат {} добавлен в черный список юзербота</b>",
        "unblacklisted": "✅ <b>Чат {} удален из черного списка юзербота</b>",
        "user_blacklisted": "✅ <b>Пользователь {} добавлен в черный список юзербота</b>",
        "user_unblacklisted": "✅ <b>Пользователь {} удален из черного списка юзербота</b>",
        "what_prefix": "❓ <b>А какой префикс ставить то?</b>",
        "prefix_incorrect": "🚫 <b>Префикс должен состоять только из одного символа</b>",
        "prefix_set": "✅ <b>Префикс обновлен. Чтобы вернуть его, используй</b> <code>{newprefix}setprefix {oldprefix}</code>",
        "alias_created": "✅ <b>Алиас создан. Используй его через</b> <code>{}</code>",
        "aliases": "<b>Алиасы:</b>\n",
        "no_command": "🚫 <b>Команда</b> <code>{}</code> <b>не существует</b>",
        "alias_args": "🚫 <b>Требуется ввести команду и алиас для нее</b>",
        "delalias_args": "🚫 <b>Требуется имя алиаса</b>",
        "alias_removed": "✅ <b>Алиас</b> <code>{}</code> <b>удален.",
        "no_alias": "<b>🚫 Алиас</b> <code>{}</code> <b>не существует</b>",
        "db_cleared": "<b>✅ База очищена</b>",
        "amore": "🌌 <b>Amore userbot</b>\n<b>Версия: {}.{}.{}</b>",
        "check_url": "🚫 <b>Укажи правильную ссылку, ведущую на пак с переводом</b>",
        "lang_saved": "{} <b>Язык сохранен!</b>",
        "pack_saved": "✅ <b>Пак перевода сохранен!</b>",
        "incorrect_language": "🚫 <b>Указан неверный язык</b>",
        "lang_removed": "✅ <b>Переводы сброшены</b>",
        "check_pack": "🚫 <b>По ссылке находится неправильный пак</b>",
        "_cmd_doc_hikka": "Показать версию Hikka",
        "_cmd_doc_blacklist": "Отключить бота где-либо",
        "_cmd_doc_unblacklist": "Включить бота где-либо",
        "_cmd_doc_blacklistuser": "Запретить пользователю выполнять все команды",
        "_cmd_doc_unblacklistuser": "Разрешить пользователю выполнять команды, на которые ему хватает разрешений",
        "_cmd_doc_setprefix": "Установить префикс",
        "_cmd_doc_aliases": "Показать алиасы",
        "_cmd_doc_addalias": "Установить алиас для команды",
        "_cmd_doc_delalias": "Удалить алиас для команды",
        "_cmd_doc_addtrnsl": "Установить пак перевода\n.addtrnsl <пак>\nТребуется перезагрузка после выполнения",
        "_cmd_doc_cleartrnsl": "Удалить все паки перевода",
        "_cmd_doc_setlang": "Выбрать предпочитаемый язык перевода\nТребуется перезагрузка после выполнения",
        "_cmd_doc_cleardb": "Сброс до заводских настроек - сброс базы данных",
        "_cls_doc": "Управление базовыми настройками юзербота",
    }

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

    async def blacklistcommon(self, message: Message):
        args = utils.get_args(message)

        if len(args) > 2:
            await utils.answer(message, self.strings("too_many_args"))
            return

        chatid = None
        module = None

        if args:
            try:
                chatid = int(args[0])
            except ValueError:
                module = args[0]

        if len(args) == 2:
            module = args[1]

        if chatid is None:
            chatid = utils.get_chat_id(message)

        module = self.allmodules.get_classname(module)
        return f"{str(chatid)}.{module}" if module else chatid

    async def hikkacmd(self, message: Message):
        """Get Hikka version"""
        await utils.answer(message, self.strings("hikka").format(*main.__version__))

    async def blacklistcmd(self, message: Message):
        """Blacklist the bot from operating somewhere"""
        chatid = await self.blacklistcommon(message)

        self._db.set(
            main.__name__,
            "blacklist_chats",
            self._db.get(main.__name__, "blacklist_chats", []) + [chatid],
        )

        await utils.answer(message, self.strings("blacklisted").format(chatid))

    async def unblacklistcmd(self, message: Message):
        """Unblacklist the bot from operating somewhere"""
        chatid = await self.blacklistcommon(message)

        self._db.set(
            main.__name__,
            "blacklist_chats",
            list(
                set(self._db.get(main.__name__, "blacklist_chats", [])) - {chatid}
            ),
        )


        await utils.answer(message, self.strings("unblacklisted").format(chatid))

    async def getuser(self, message: Message):
        try:
            return int(utils.get_args(message)[0])
        except (ValueError, IndexError):
            reply = await message.get_reply_message()

            if reply:
                return reply.sender_id

            if message.is_private:
                return message.to_id.user_id

            await utils.answer(message, self.strings("who_to_unblacklist"))
            return

    async def blacklistusercmd(self, message: Message):
        """Prevent this user from running any commands"""
        user = await self.getuser(message)

        self._db.set(
            main.__name__,
            "blacklist_users",
            self._db.get(main.__name__, "blacklist_users", []) + [user],
        )

        await utils.answer(message, self.strings("user_blacklisted").format(user))

    async def unblacklistusercmd(self, message: Message):
        """Allow this user to run permitted commands"""
        user = await self.getuser(message)

        self._db.set(
            main.__name__,
            "blacklist_users",
            list(set(self._db.get(main.__name__, "blacklist_users", [])) - {user}),
        )


        await utils.answer(
            message,
            self.strings("user_unblacklisted").format(user),
        )

    @loader.owner
    async def setprefixcmd(self, message: Message):
        """Sets command prefix"""
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, self.strings("what_prefix"))
            return

        if len(args) != 1:
            await utils.answer(message, self.strings("prefix_incorrect"))
            return

        oldprefix = self.get_prefix()
        self._db.set(main.__name__, "command_prefix", args)
        await utils.answer(
            message,
            self.strings("prefix_set").format(
                newprefix=utils.escape_html(args[0]),
                oldprefix=utils.escape_html(oldprefix),
            ),
        )

    @loader.owner
    async def aliasescmd(self, message: Message):
        """Print all your aliases"""
        aliases = self.allmodules.aliases
        string = self.strings("aliases")

        string += "\n".join([f"\n{i}: {y}" for i, y in aliases.items()])

        await utils.answer(message, string)

    @loader.owner
    async def addaliascmd(self, message: Message):
        """Set an alias for a command"""
        args = utils.get_args(message)

        if len(args) != 2:
            await utils.answer(message, self.strings("alias_args"))
            return

        alias, cmd = args
        if ret := self.allmodules.add_alias(alias, cmd):
            self._db.set(
                __name__,
                "aliases",
                {
                    **self._db.get(__name__, "aliases"),
                    alias: cmd,
                },
            )
            await utils.answer(
                message,
                self.strings("alias_created").format(utils.escape_html(alias)),
            )
        else:
            await utils.answer(
                message,
                self.strings("no_command").format(utils.escape_html(cmd)),
            )

    @loader.owner
    async def delaliascmd(self, message: Message):
        """Remove an alias for a command"""
        args = utils.get_args(message)

        if len(args) != 1:
            await utils.answer(message, self.strings("delalias_args"))
            return

        alias = args[0]
        if ret := self.allmodules.remove_alias(alias):
            current = self._db.get(__name__, "aliases")
            del current[alias]
            self._db.set(__name__, "aliases", current)
            await utils.answer(
                message,
                self.strings("alias_removed").format(utils.escape_html(alias)),
            )
        else:
            await utils.answer(
                message,
                self.strings("no_alias").format(utils.escape_html(alias)),
            )

    async def dllangpackcmd(self, message: Message):
        """[link to a langpack | empty to remove] - Change Hikka translate pack (external)"""
        args = utils.get_args_raw(message)

        if not args:
            self._db.set(translations.__name__, "pack", False)
            await self.translator.init()
            await utils.answer(message, self.strings("lang_removed"))
            return

        if not utils.check_url(args):
            await utils.answer(message, self.strings("check_url"))
            return

        self._db.set(translations.__name__, "pack", args)
        success = await self.translator.init()
        await utils.answer(
            message, self.strings("pack_saved" if success else "check_pack")
        )

    async def setlangcmd(self, message: Message):
        """[language] - Change default language"""
        args = utils.get_args_raw(message)
        if not args or len(args) != 2:
            await utils.answer(message, self.strings("incorrect_language"))
            return

        possible_pack_path = os.path.join(
            utils.get_base_dir(),
            f"langpacks/{args.lower()}.json",
        )

        if os.path.isfile(possible_pack_path):
            self._db.set(translations.__name__, "pack", args.lower())

        self._db.set(translations.__name__, "lang", args.lower())
        await self.translator.init()

        await utils.answer(
            message,
            self.strings("lang_saved").format(
                utils.get_lang_flag(args.lower() if args.lower() != "en" else "gb")
            ),
        )

    @loader.owner
    async def cleardbcmd(self, message: Message):
        """Clears the entire database, effectively performing a factory reset"""
        self._db.clear()
        self._db.save()
        await utils.answer(message, self.strings("db_cleared"))

    async def _client_ready2(self, client, db):  # skicpq: PYL-W0613
        ret = {
            alias: cmd
            for alias, cmd in db.get(__name__, "aliases", {}).items()
            if self.allmodules.add_alias(alias, cmd)
        }

        db.set(__name__, "aliases", ret)
