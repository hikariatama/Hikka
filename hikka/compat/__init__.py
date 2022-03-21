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

import logging
import sys
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec

from .raphielgang import RaphielgangConfig, RaphielgangEvents, RaphielgangDatabase
from .uniborg import UniborgUtil, Uniborg

# When a name is matched, the import is overriden, and our custom object is returned
MODULES = {
    "userbot": RaphielgangConfig,
    "userbot.events": RaphielgangEvents,
    "userbot.modules": RaphielgangConfig,
    "userbot.modules.dbhelper": RaphielgangDatabase,
    "uniborg": Uniborg,
    "uniborg.util": UniborgUtil,
}


class BotCompat(
    MetaPathFinder, Loader
):  # pylint: disable=W0223 # It's wrong - https://kutt.it/hkjRb9
    """importlib Loader that loads the classes in MODULES under their pseudonyms"""

    def __init__(self, clients):
        self.clients = clients
        self.created = []

    def find_spec(self, fullname, path, target=None):
        """https://docs.python.org/3.7/library/importlib.html#importlib.abc.MetaPathFinder.find_spec"""
        return ModuleSpec(fullname, self) if fullname in MODULES else None

    def create_module(self, spec):
        """https://docs.python.org/3.7/library/importlib.html#importlib.abc.Loader.create_module"""
        ret = MODULES[spec.name](self.clients)
        self.created += [ret]
        return ret

    @staticmethod
    def exec_module(module):
        """https://docs.python.org/3.7/library/importlib.html#importlib.abc.Loader.exec_module"""
        module.__path__ = []

    async def client_ready(self, client):
        """Signal all mods that client_ready()"""
        self.clients += [client]
        for mod in self.created:
            try:
                await mod.client_ready(client)
            except BaseException as e:
                logging.exception(
                    "Failed to send client_ready to compat layer "
                    + repr(mod)
                    + f"due to {e}"
                )


def activate(clients):
    """Activate the compat layer"""
    compatlayer = BotCompat(clients)
    sys.meta_path.insert(0, compatlayer)
    return compatlayer
