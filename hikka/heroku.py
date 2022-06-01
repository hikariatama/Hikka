"""Handles heroku uploads"""

from collections import namedtuple
import logging
import os

import heroku3

from git import Repo
from git.exc import InvalidGitRepositoryError
from typing import Optional

from . import utils


def publish(
    key: Optional[str] = None,
    api_token: Optional[str] = None,
    create_new: Optional[bool] = True,
):
    """Push to heroku"""
    logging.debug("Configuring heroku...")

    if key is None:
        key = os.environ.get("heroku_api_token")

    app, config = get_app(key, api_token, create_new)

    config["heroku_api_token"] = key

    if api_token is not None:
        config["api_id"] = api_token.ID
        config["api_hash"] = api_token.HASH

    app.update_buildpacks(
        [
            "https://github.com/heroku/heroku-buildpack-python",
            "https://github.com/hikariatama/heroku-buildpack",
            "https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest",
            "https://github.com/jontewks/puppeteer-heroku-buildpack",
            "https://github.com/heroku/heroku-buildpack-apt",
        ]
    )

    if not any(
        addon.plan.name.startswith("heroku-buildpack-") for addon in app.addons()
    ):
        app.install_addon("heroku-postgresql")

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
    key: Optional[str] = None,
    api_token: Optional[namedtuple] = None,
    create_new: Optional[bool] = True,
):
    if key is None:
        key = os.environ.get("heroku_api_token")

    heroku = heroku3.from_key(key)

    for poss_app in heroku.apps():
        config = poss_app.config()

        if api_token is None or (
            config["api_id"] == api_token.ID and config["api_hash"] == api_token.HASH
        ):
            return app, config

    if not create_new:
        logging.error("%r", {app: repr(app.config) for app in heroku.apps()})
        raise RuntimeError("Could not identify app!")

    app = heroku.create_app(
        name=f"hikka-{utils.rand(8)}",
        stack_id_or_name="heroku-20",
        region_id_or_name="eu",
    )

    config = app.config()

    return app, config


def get_repo():
    """Helper to get the repo, making it if not found"""
    try:
        repo = Repo(os.path.dirname(utils.get_base_dir()))
    except InvalidGitRepositoryError:
        repo = Repo.init(os.path.dirname(utils.get_base_dir()))
        origin = repo.create_remote(
            "origin",
            "https://github.com/hikariatama/Hikka",
        )
        origin.fetch()
        repo.create_head("master", origin.refs.master)
        repo.heads.master.set_tracking_branch(origin.refs.master)
        repo.heads.master.checkout(True)
    return repo


def init():
    """Will be run on every Heroku start"""
    # Create repo if not found
    get_repo()
