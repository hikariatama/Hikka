__version__ = (1, 0, 3)

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://static.dan.tatar/spotify_icon.png
# meta banner: https://mods.hikariatama.ru/badges/spotify.jpg
# meta developer: @hikarimods
# scope: hikka_only
# scope: hikka_min 1.2.10
# requires: spotipy Pillow

import asyncio
import contextlib
import functools
import io
import logging
import re
import time
import traceback
from math import ceil
from types import FunctionType

import requests
import spotipy
from hikkatl.errors.rpcerrorlist import FloodWaitError
from hikkatl.tl.functions.account import UpdateProfileRequest
from hikkatl.tl.types import Message
from PIL import Image, ImageDraw, ImageFont

from .. import loader, utils

logger = logging.getLogger(__name__)
logging.getLogger("spotipy").setLevel(logging.CRITICAL)


SIZE = (1200, 320)
INNER_MARGIN = (16, 16)

TRACK_FS = 48
ARTIST_FS = 32


@loader.tds
class SpotifyMod(loader.Module):
    """Display beautiful spotify now bar. Idea: t.me/fuccsoc. Implementation: t.me/hikariatama"""

    strings = {
        "name": "SpotifyNow",
        "need_auth": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Call"
            " </b><code>.sauth</code><b> before using this action.</b>"
        ),
        "on-repeat": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>Set on-repeat.</b>"
        ),
        "off-repeat": (
            "<emoji document_id=5472354553527541051>✋</emoji> <b>Stopped track"
            " repeat.</b>"
        ),
        "skipped": (
            "<emoji document_id=5471978009449731768>👉</emoji> <b>Skipped track.</b>"
        ),
        "err": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Error occurred. Make"
            " sure the track is playing!</b>\n<code>{}</code>"
        ),
        "already_authed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>You are already"
            " authentificated</b>"
        ),
        "authed": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Auth successful</b>"
        ),
        "playing": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Playing...</b>"
        ),
        "back": (
            "<emoji document_id=5469735272017043817>👈</emoji> <b>Switched to previous"
            " track</b>"
        ),
        "paused": "<emoji document_id=5469904794376217131>🤚</emoji> <b>Pause</b>",
        "deauth": (
            "<emoji document_id=6037460928423791421>🚪</emoji> <b>Unauthentificated</b>"
        ),
        "restarted": (
            "<emoji document_id=5469735272017043817>👈</emoji> <b>Playing track"
            " from the"
            " beginning</b>"
        ),
        "auth": (
            '<emoji document_id=5472308992514464048>🔐</emoji> <a href="{}">Proceed'
            " here</a>, approve request, then <code>.scode https://...</code> with"
            " redirected url"
        ),
        "liked": (
            "<emoji document_id=5199727145022134809>❤️</emoji> <b>Liked current"
            " playback</b>"
        ),
        "autobio": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Spotify autobio"
            " {}</b>"
        ),
        "404": "<emoji document_id=5312526098750252863>🚫</emoji> <b>No results</b>",
        "playing_track": (
            "<emoji document_id=5212941939053175244>🎧</emoji> <b>{} added to queue</b>"
        ),
        "no_music": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>No music is"
            " playing!</b>"
        ),
        "searching": (
            "<emoji document_id=5188311512791393083>🔎</emoji> <b>Searching...</b>"
        ),
        "currently_on": "Currently listening on",
        "playlist": "Playlist",
        "owner": "Owner",
        "quality": "Quality",
    }

    strings_ru = {
        "need_auth": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Выполни"
            " </b><code>.sauth</code><b> перед выполнением этого действия.</b>"
        ),
        "on-repeat": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>Повторение"
            " включено.</b>"
        ),
        "off-repeat": (
            "<emoji document_id=5472354553527541051>✋</emoji> <b>Повторение"
            " выключено.</b>"
        ),
        "skipped": (
            "<emoji document_id=5471978009449731768>👉</emoji> <b>Трек переключен.</b>"
        ),
        "err": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Произошла ошибка."
            " Убедитесь, что музыка играет!</b>\n<code>{}</code>"
        ),
        "already_authed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Уже авторизован</b>"
        ),
        "authed": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Успешная"
            " аутентификация</b>"
        ),
        "playing": "<emoji document_id=6319076999105087378>🎧</emoji> <b>Играю...</b>",
        "back": (
            "<emoji document_id=5469735272017043817>👈</emoji> <b>Переключил назад</b>"
        ),
        "paused": "<emoji document_id=5469904794376217131>🤚</emoji> <b>Пауза</b>",
        "deauth": (
            "<emoji document_id=6037460928423791421>🚪</emoji> <b>Авторизация"
            " отменена</b>"
        ),
        "restarted": (
            "<emoji document_id=5469735272017043817>👈</emoji> <b>Начал трек"
            " сначала</b>"
        ),
        "liked": (
            '<emoji document_id=5199727145022134809>❤️</emoji> <b>Поставил "Мне'
            ' нравится" текущему треку</b>'
        ),
        "autobio": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Обновление био"
            " включено {}</b>"
        ),
        "404": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Нет результатов</b>"
        ),
        "playing_track": (
            "<emoji document_id=5212941939053175244>🎧</emoji> <b>{} добавлен в"
            " очередь</b>"
        ),
        "no_music": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Музыка не играет!</b>"
        ),
        "_cmd_doc_sfind": "Найти информацию о треке",
        "_cmd_doc_sauth": "Первый этап аутентификации",
        "_cmd_doc_scode": "Второй этап аутентификации",
        "_cmd_doc_unauth": "Отменить аутентификацию",
        "_cmd_doc_sbio": "Включить автоматическое био",
        "_cmd_doc_stokrefresh": "Принудительное обновление токена",
        "_cmd_doc_snow": "Показать карточку текущего трека",
        "_cls_doc": (
            "Тулкит для Spotify. Автор идеи: @fuccsoc. Реализация: @hikariatama"
        ),
        "currently_on": "Сейчас слушаю на",
        "playlist": "Плейлист",
        "owner": "Владелец",
        "quality": "Качество",
    }

    strings_de = {
        "need_auth": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Führe"
            " </b><code>.sauth</code><b> aus, bevor du diese Aktion ausführst.</b>"
        ),
        "on-repeat": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>Wiederholung"
            " aktiviert.</b>"
        ),
        "off-repeat": (
            "<emoji document_id=5472354553527541051>✋</emoji> <b>Wiederholung"
            " deaktiviert.</b>"
        ),
        "skipped": (
            "<emoji document_id=5471978009449731768>👉</emoji> <b>Track"
            " übersprungen.</b>"
        ),
        "err": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Ein Fehler ist"
            " aufgetreten. Stelle sicher, dass eine Musik abgespielt"
            " wird!</b>\n<code>{}</code>"
        ),
        "already_authed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Bereits"
            " authentifiziert</b>"
        ),
        "authed": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Authentifizierung"
            " erfolgreich</b>"
        ),
        "playing": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Spielt ab...</b>"
        ),
        "back": (
            "<emoji document_id=5469735272017043817>👈</emoji> <b>Zum vorherigen Track"
            " gewechselt</b>"
        ),
        "paused": "<emoji document_id=5469904794376217131>🤚</emoji> <b>Pausiert</b>",
        "deauth": (
            "<emoji document_id=6037460928423791421>🚪</emoji> <b>Authentifizierung"
            " aufgehoben</b>"
        ),
        "restarted": (
            "<emoji document_id=5469735272017043817>👈</emoji> <b>Track von vorne"
            " gestartet</b>"
        ),
        "liked": (
            "<emoji document_id=5199727145022134809>❤️</emoji> <b>Der aktuelle Track"
            " wurde geliked</b>"
        ),
        "autobio": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Spotify Autobio"
            " {}</b>"
        ),
        "404": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Keine Ergebnisse</b>"
        ),
        "playing_track": (
            "<emoji document_id=5212941939053175244>🎧</emoji> <b>{} zur Warteschlange"
            " hinzugefügt</b>"
        ),
        "no_music": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Es wird keine Musik"
            " abgespielt!</b>"
        ),
        "_cmd_doc_sfind": "Finde Informationen über einen Track",
        "_cmd_doc_sauth": "Erster Schritt der Authentifizierung",
        "_cmd_doc_scode": "Zweiter Schritt der Authentifizierung",
        "_cmd_doc_unauth": "Authentifizierung aufheben",
        "_cmd_doc_sbio": "Spotify Autobio aktivieren",
        "_cmd_doc_stokrefresh": "Token erzwingen",
        "_cmd_doc_snow": "Zeige die Karte des aktuellen Tracks",
        "_cls_doc": (
            "Toolkit für Spotify. Idee von: @fuccsoc. Implementierung von: @hikariatama"
        ),
        "currently_on": "Aktuell auf",
        "playlist": "Wiedergabeliste",
        "owner": "Besitzer",
        "quality": "Qualität",
    }

    strings_tr = {
        "need_auth": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Bu eylemi"
            " gerçekleştirmeden önce </b><code>.sauth</code><b> komutunu kullanın.</b>"
        ),
        "on-repeat": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>Tekrar açık.</b>"
        ),
        "off-repeat": (
            "<emoji document_id=5472354553527541051>✋</emoji> <b>Tekrar kapalı.</b>"
        ),
        "skipped": (
            "<emoji document_id=5471978009449731768>👉</emoji> <b>Şarkı atlandı.</b>"
        ),
        "err": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Bir hata oluştu."
            " Müzik"
            " çalmak istediğinizden emin olun!</b>\n<code>{}</code>"
        ),
        "already_authed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Zaten"
            " yetkilendirildi</b>"
        ),
        "authed": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Yetkilendirme"
            " başarılı</b>"
        ),
        "playing": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Oynatılıyor...</b>"
        ),
        "back": (
            "<emoji document_id=5469735272017043817>👈</emoji> <b>Önceki şarkıya"
            " geçildi</b>"
        ),
        "paused": (
            "<emoji document_id=5469904794376217131>🤚</emoji> <b>Duraklatıldı</b>"
        ),
        "deauth": (
            "<emoji document_id=6037460928423791421>🚪</emoji> <b>Yetkilendirme iptal"
            " edildi</b>"
        ),
        "restarted": (
            "<emoji document_id=5469735272017043817>👈</emoji> <b>Şarkı tekrar"
            " başlatıldı</b>"
        ),
        "liked": (
            "<emoji document_id=5199727145022134809>❤️</emoji> <b>Geçerli şarkı"
            " beğenildi</b>"
        ),
        "autobio": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Spotify Otomatik Bio"
            " {}</b>"
        ),
        "404": "<emoji document_id=5312526098750252863>🚫</emoji> <b>Sonuç yok</b>",
        "playing_track": (
            "<emoji document_id=5212941939053175244>🎧</emoji> <b>{} kuyruğa"
            " eklendi</b>"
        ),
        "no_music": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Şu anda müzik"
            " çalmıyor!</b>"
        ),
        "_cmd_doc_sfind": "Bir şarkı hakkında bilgi bul",
        "_cmd_doc_sauth": "Yetkilendirme için ilk adım",
        "_cmd_doc_scode": "Yetkilendirme için ikinci adım",
        "_cmd_doc_unauth": "Yetkilendirmeyi kaldır",
        "_cmd_doc_sbio": "Spotify Otomatik Bio etkinleştir",
        "_cmd_doc_stokrefresh": "Zorla token yenile",
        "_cmd_doc_snow": "Geçerli şarkı kartını göster",
        "_cls_doc": "Spotify için bir araç. Fikir: @fuccsoc. Uygulama: @hikariatama",
        "currently_on": "Şu anda dinleniyor",
        "playlist": "Çalma listesi",
        "owner": "Sahibi",
        "quality": "Kalite",
    }

    strings_uz = {
        "need_auth": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Bu harakatni"
            " bajarishdan oldin </b><code>.sauth</code><b> buyrug'ini ishlating.</b>"
        ),
        "on-repeat": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>Takror yoqilgan.</b>"
        ),
        "off-repeat": (
            "<emoji document_id=5472354553527541051>✋</emoji> <b>Takror yopilgan.</b>"
        ),
        "skipped": (
            "<emoji document_id=5471978009449731768>👉</emoji> <b>Mashq o'tkazildi.</b>"
        ),
        "err": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Xatolik yuz berdi."
            " Muzyka oynatilganiga ishonchingiz komilmi?</b>\n<code>{}</code>"
        ),
        "already_authed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Allaqachon"
            " tasdiqlangan</b>"
        ),
        "authed": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Tasdiqlash"
            " muvaffaqiyatli bajarildi</b>"
        ),
        "playing": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Oynatilmoqda...</b>"
        ),
        "back": (
            "<emoji document_id=5469735272017043817>👈</emoji> <b>Oldingi mashqa"
            " o'tildi</b>"
        ),
        "paused": (
            "<emoji document_id=5469904794376217131>🤚</emoji> <b>To'xtatildi</b>"
        ),
        "deauth": (
            "<emoji document_id=6037460928423791421>🚪</emoji> <b>Tasdiqlash bekor"
            " qilindi</b>"
        ),
        "restarted": (
            "<emoji document_id=5469735272017043817>👈</emoji> <b>Mashq qayta"
            " boshlandi</b>"
        ),
        "liked": (
            "<emoji document_id=5199727145022134809>❤️</emoji> <b>Joriy mashq"
            " yoqildi</b>"
        ),
        "autobio": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Spotify Avtomatik Bio"
            " {}</b>"
        ),
        "404": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Natija topilmadi</b>"
        ),
        "playing_track": (
            "<emoji document_id=5212941939053175244>🎧</emoji> <b>{} qo'shildi</b>"
        ),
        "no_music": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Hozircha hech qanday"
            " musiqa oynatilmoqda emas!</b>"
        ),
        "_cmd_doc_sfind": "Mashq haqida ma'lumot toping",
        "_cmd_doc_sauth": "Tasdiqlash uchun birinchi qadam",
        "_cmd_doc_scode": "Tasdiqlash uchun ikkinchi qadam",
        "_cmd_doc_unauth": "Tasdiqlashni bekor qilish",
        "_cmd_doc_sbio": "Spotify Avtomatik Bio yoqish",
        "_cmd_doc_stokrefresh": "Tokenni qo'lda qayta tiklash",
        "_cmd_doc_snow": "Joriy mashq kartasini ko'rsatish",
        "_cls_doc": "Spotify uchun asbob. Fikr: @fuccsoc. Tuzilishi: @hikariatama",
        "currently_on": "Hozircha",
        "playlist": "O'ynatiladiganlar",
        "owner": "Sahibi",
        "quality": "Sifat",
    }

    strings_es = {
        "need_auth": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Para usar este"
            " comando, primero usa </b><code>.sauth</code><b>.</b>"
        ),
        "on-repeat": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>Reproducción en bucle"
            " activada.</b>"
        ),
        "off-repeat": (
            "<emoji document_id=5472354553527541051>✋</emoji> <b>Reproducción en bucle"
            " desactivada.</b>"
        ),
        "skipped": (
            "<emoji document_id=5471978009449731768>👉</emoji> <b>Pista saltada.</b>"
        ),
        "err": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Ha ocurrido un error."
            " ¿Estás seguro de que hay música sonando?</b>\n<code>{}</code>"
        ),
        "already_authed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Ya autorizado</b>"
        ),
        "authed": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Autorizado"
            " correctamente</b>"
        ),
        "playing": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Reproduciendo...</b>"
        ),
        "back": (
            "<emoji document_id=5469735272017043817>👈</emoji> <b>Volviste a la pista"
            " anterior</b>"
        ),
        "paused": "<emoji document_id=5469904794376217131>🤚</emoji> <b>Pausado</b>",
        "deauth": (
            "<emoji document_id=6037460928423791421>🚪</emoji> <b>Autorización"
            " desactivada</b>"
        ),
        "restarted": (
            "<emoji document_id=5469735272017043817>👈</emoji> <b>Pista reiniciada</b>"
        ),
        "liked": (
            "<emoji document_id=5199727145022134809>❤️</emoji> <b>Pista actual"
            " añadida a favoritos</b>"
        ),
        "autobio": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Spotify Auto Bio"
            " {}</b>"
        ),
        "404": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>No se encontraron"
            " resultados</b>"
        ),
        "playing_track": (
            "<emoji document_id=5212941939053175244>🎧</emoji> <b>{} añadido</b>"
        ),
        "no_music": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>¡No hay música"
            " actualmente!</b>"
        ),
        "_cmd_doc_sfind": "Encuentra información sobre una canción",
        "_cmd_doc_sauth": "Primer paso para autorizar",
        "_cmd_doc_scode": "Segundo paso para autorizar",
        "_cmd_doc_unauth": "Desautorizar",
        "_cmd_doc_sbio": "Activar Auto Bio de Spotify",
        "_cmd_doc_stokrefresh": "Actualizar token en segundo plano",
        "_cmd_doc_snow": "Muestra la tarjeta de la canción actual",
        "_cls_doc": "Recursos para Spotify. Idea: @fuccsoc. Creado por: @hikariatama",
        "currently_on": "Escuchando actualmente en",
        "playlist": "Lista de reproducción",
        "owner": "Propietario",
        "quality": "Calidad",
    }

    def __init__(self):
        self._client_id = "e0708753ab60499c89ce263de9b4f57a"
        self._client_secret = "80c927166c664ee98a43a2c0e2981b4a"
        self.scope = (
            "user-read-playback-state playlist-read-private playlist-read-collaborative"
            " app-remote-control user-modify-playback-state user-library-modify"
            " user-library-read"
        )
        self.sp_auth = spotipy.oauth2.SpotifyOAuth(
            client_id=self._client_id,
            client_secret=self._client_secret,
            redirect_uri="https://thefsch.github.io/spotify/",
            scope=self.scope,
        )
        self.config = loader.ModuleConfig(
   
