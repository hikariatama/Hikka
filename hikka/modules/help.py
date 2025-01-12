from hikkatl.tl.types import Message

from .. import loader, utils


@loader.tds
class HelpMod(loader.Module):
    """Shows installed modules and their commands"""

    strings = {"name": "Help", "header": "<b>Modules:</b>\n\n"}

    @loader.command(alias="modules")
    async def helpicmd(self, message: Message):
        """Shows available modules and their commands."""
        output = self.strings["header"]
        modules = sorted(
            self.allmodules.modules, key=lambda m: m.strings.get("name", "Unknown")
        )

        for module in modules:
            name = module.strings.get("name", "Unknown")
            emoji = "<emoji document_id=5893431652578758294>✅</emoji>"
            commands = []
            for cmd_name, cmd_func in module.commands.items():
                if not cmd_func:
                   continue
                full_command = f"{self.get_prefix()}{cmd_name}"
                commands.append(
                    f"{utils.escape_html(full_command)}"
                )
            if commands:
                output += f"<b>{emoji} {name}</b>: {', '.join(commands)}\n\n"
            else:
                output += f"<b>{emoji} {name}</b>:\n\n"
        await utils.answer(message, output)





