from hikkatl.tl.types import Message

from .. import loader, utils


@loader.tds
class HyeKo(loader.Module):
    """Sends a HYEKO"""

    strings = {"name": "HyeKo"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "photo_url",
                "https://0x0.st/s/tsQb8iTZtcxstKQNujOL_w/8oiU.jpg",  
                lambda: self.strings("_cfg_photo_url"),
                validator=loader.validators.Link(),
            )
        )

    @loader.command()
    async def hyeko(self, message: Message):
        """Sends the HyeKo message with a photo"""
        text = (
            "<emoji document_id=5893431652578758294>✅</emoji>HYEKO\n"
            "<emoji document_id=5893431652578758294>✅</emoji>Version: 1.6.5\n"
            "<emoji document_id=5893431652578758294>✅</emoji>Forked: @arioncheck\n"
            "<emoji document_id=5893431652578758294>✅</emoji>Design: @arioncheck"
        )
        
        await utils.answer_file(message, self.config["photo_url"], text)
