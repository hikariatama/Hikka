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

"""Initial entrypoint"""

import sys
import getpass
import os

if getpass.getuser() == "root" and "--root" not in " ".join(sys.argv):
    print("!" * 30)
    print("NEVER EVER RUN USERBOT FROM ROOT")
    print("THIS IS THE THREAD FOR NOT ONLY YOUR DATA, ")
    print("BUT ALSO FOR YOUR DEVICE ITSELF!")
    print("!" * 30)
    print()
    print("TYPE force_insecure TO IGNORE THIS WARNING")
    print("TYPE ANYTHING ELSE TO EXIT:")
    if input("> ").lower() != "force_insecure":
        sys.exit(1)

if sys.version_info < (3, 8, 0):
    print("Error: you must use at least Python version 3.8.0")  # pragma: no cover
elif __package__ != "friendly-telegram":  # In case they did python __main__.py
    print(
        "Error: you cannot run this as a script; you must execute as a package"
    )  # pragma: no cover
else:
    from . import log

    log.init()
    try:
        from . import main
    except ModuleNotFoundError:  # pragma: no cover
        print(
            "Error: you have not installed all dependencies correctly.\n"
            "Attempting dependencies installation... Just wait."
        )

        os.popen("pip3 install -r requirements.txt").read()  # skipcq: BAN-B605, BAN-B607

        try:
            from . import main
        except ModuleNotFoundError:
            print(
                "Error while installing dependencies. Please, do this manually!\n"
                "pip3 install -r requirements.txt"
            )

            sys.exit(1)

    if __name__ == "__main__":
        main.main()  # Execute main function
