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

"""Handles heroku uploads"""

import json
import logging
import os

import heroku3
from git import Repo
from git.exc import InvalidGitRepositoryError
from telethon.sessions import StringSession

from . import utils


def publish(clients, key, api_token=None, create_new=True, full_match=False):
    """Push to heroku"""
    logging.debug("Configuring heroku...")

    data = json.dumps(
        {
            getattr(client, "phone", ""): StringSession.save(client.session)
            for client in clients
        }
    )
    app, config = get_app(data, key, api_token, create_new, full_match)

    config["authorization_strings"] = data
    config["heroku_api_token"] = key

    if api_token is not None:
        config["api_id"] = api_token.ID
        config["api_hash"] = api_token.HASH

    app.update_buildpacks(
        [
            "https://github.com/heroku/heroku-buildpack-python",
            "https://github.com/GeekTG/Heroku-BuildPack",
            "https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest",
        ]
    )

    repo = get_repo()
    url = app.git_url.replace("https://", f"https://api:{key}@")

    if "heroku" in repo.remotes:
        remote = repo.remote("heroku")
        remote.set_url(url)
    else:
        remote = repo.create_remote("heroku", url)

    remote.push(refspec="HEAD:refs/heads/master")

    return app


def get_app(
    authorization_strings, key, api_token=None, create_new=True, full_match=False
):
    heroku = heroku3.from_key(key)
    app = None

    for poss_app in heroku.apps():
        config = poss_app.config()

        if "authorization_strings" not in config:
            continue

        if api_token is None or (
            config["api_id"] == api_token.ID and config["api_hash"] == api_token.HASH
        ):
            if full_match and config["authorization_strings"] != authorization_strings:
                continue

            app = poss_app
            break

    if app is None:
        if api_token is None or not create_new:
            logging.error("%r", {app: repr(app.config) for app in heroku.apps()})
            raise RuntimeError("Could not identify app!")

        app = heroku.create_app(stack_id_or_name="heroku-18", region_id_or_name="us")
        config = app.config()

    return app, config


def get_repo():
    """Helper to get the repo, making it if not found"""
    try:
        repo = Repo(os.path.dirname(utils.get_base_dir()))
    except InvalidGitRepositoryError:
        repo = Repo.init(os.path.dirname(utils.get_base_dir()))
        origin = repo.create_remote(
            "origin", "https://github.com/GeekTG/Friendly-Telegram"
        )
        origin.fetch()
        repo.create_head("master", origin.refs.master)
        repo.heads.master.set_tracking_branch(origin.refs.master)
        repo.heads.master.checkout(True)
    return repo
