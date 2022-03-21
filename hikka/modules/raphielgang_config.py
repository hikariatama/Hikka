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

#    Modded by GeekTG Team

import itertools
import logging

import userbot  # see .compat

from .. import loader

logger = logging.getLogger(__name__)


@loader.tds
class RaphielgangConfigMod(loader.Module):
    """Stores configuration for Raphielgang modules"""

    strings = {
        "name": "Raphielgang Configuration Placeholder",
        "cfg_doc": "External configuration item",
    }

    def __init__(self):
        self.config = filter(lambda x: len(x) and x.upper() == x, userbot.__all__)
        self.config = loader.ModuleConfig(
            *itertools.chain.from_iterable(
                [(x, None, lambda m: self.strings("cfg_doc", m)) for x in self.config]
            )
        )

    def config_complete(self):
        for key, value in self.config.items():
            if value is not None:
                setattr(userbot, key, value)
