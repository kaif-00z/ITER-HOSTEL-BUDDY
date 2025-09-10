#    This file is part of the ITER Hostel Buddy distribution.
#    Copyright (c) 2025 kAiF_00z
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#    General Public License for more details.
#
# License can be found in <
# https://github.com/kaif-00z/ITER-HOSTEL-BUDDY/blob/main/LICENSE > .

# if you are using this following code then don't forgot to give proper authorship or
# credit to t.me/kAiF_00z (github.com/kaif-00z)


import asyncio
import json
import random
from datetime import datetime, timedelta

import aiofiles
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from decouple import config
from telethon import Button, TelegramClient, events
from telethon.utils import get_display_name

from data.timing import TIMING
from db import DataBase
from func import run_async, ts
from strings import ABOUT, EMOJI, QTS, TXT


class Var:
    BOT_TOKEN = config("BOT_TOKEN")
    MONGO_SRV = config("MONGO_SRV")
    ADMINS = (config("ADMINS", default=",")).split(",")


bot = TelegramClient(None, api_id=6, api_hash="eb06d4abfb49dc3eeb1aeb98ae0f581e")
dB = DataBase(Var.MONGO_SRV)
sch = AsyncIOScheduler(timezone="Asia/Kolkata")
UPTIME = datetime.now(pytz.timezone("Asia/Kolkata"))

# actually doesn't make any sense if deployed on restarting server (like heroku, koyeb, railway, etc)
# but it make sense if its deployed on non restarting server
# so that we don't need to load menu again and again :)
DATA = {"BOYS": {}, "GIRLS": {}}

# ahh, no need of try , except cause program will crash in startup if
# something went wrong...


async def start_bot() -> None:

    # too lazy to warp it into a function so emjoy
    print("Loading Static Menu Files....")
    async with aiofiles.open("data/W-BH 1-12.json", "r", encoding="utf-8") as f:
        DATA["BOYS"] = json.loads(await f.read())
    async with aiofiles.open("data/W-LH 1-4.json", "r", encoding="utf-8") as f:
        DATA["GIRLS"] = json.loads(await f.read())
    print("Successfully Loaded Static Menu Files!")

    await bot.start(bot_token=Var.BOT_TOKEN)
    bot.me = await bot.get_me()
    print(f"@{bot.me.username} is Online Now.")


@run_async  # not just dummy async
def menu_today(tmrw=None):
    data = {"BOYS": {}, "GIRLS": {}}
    for (
        key
    ) in (
        DATA.keys()
    ):  # better to copy the orginial DATA var as if we change something in loop it will give error, but here we aren't modifying anything , ye boiiiii
        dt = (
            datetime.now(pytz.timezone("Asia/Kolkata")) + timedelta(days=1)
            if tmrw
            else datetime.now(pytz.timezone("Asia/Kolkata"))
        )
        data[key] = DATA[key]["weeks"][(dt.isocalendar()[1]) % 4]["days"][dt.weekday()]
    return data


bot.loop.run_until_complete(start_bot())


async def broadcast(gen, txt):
    users = await dB.get_menu_notify_user(gen)
    for user in users:
        try:
            await bot.send_message(int(user), txt)
            await asyncio.sleep(0.2)
        except BaseException as ex:
            print(ex)


async def scheduled_notify(what_is: str):
    TODAY = await menu_today()  # to make sure that we have latest menu
    for key in TODAY.keys():
        text = TXT.format(
            EMOJI[what_is],
            what_is.title(),
            TIMING[what_is][0],
            TODAY[key][what_is].title(),
        )
        text = "\n\n".join(text.split("\n"))
        text += f"`{random.choice(QTS)}`"
        await broadcast(key, text)


@bot.on(
    events.NewMessage(incoming=True, pattern="^/start", func=lambda e: e.is_private)
)
async def _start(e):
    await e.reply(
        f"Hey `{get_display_name(e.sender)}`\nI Will Notify You With Menu and Timing Of **ITER HOSTELS MESS**\n\n__Please Select Your Gender Below 👇__\n\n__NOTE: ReSelecting Will Override The Previous Selection!!__",
        buttons=[
            [
                Button.inline("👨 BOYS HOSTEL", data=f"male_{e.sender_id}"),
                Button.inline("👩 GIRLS HOSTEL", data=f"female_{e.sender_id}"),
            ]
        ],
    )

async def _tell_to_select_hostel(e, _id):
    await e.edit(
        f"__Sorry!__\n\n__You Haven't Selected Your Hostel Yet!__\n__Please Select Your Hostel First Then Use The Following Command!!__",
        buttons=[
            [
                Button.inline("👨 BOYS HOSTEL", data=f"male_{_id}"),
                Button.inline("👩 GIRLS HOSTEL", data=f"female_{_id}"),
            ]
        ],
    )

@bot.on(
    events.NewMessage(incoming=True, pattern="^/today", func=lambda e: e.is_private)
)
async def _today(e):
    xn = await e.reply("`Getting Menu For You.... 🔍`")
    if user_data := await dB.get_user_info(e.sender_id):
        TODAY = await menu_today()  # to make sure that we have latest menu
        gender_batao = user_data.get("gender")
        txt = f"**📋 Today Menu & Timing ⏰** __({
            datetime.now(
                pytz.timezone('Asia/Kolkata')).strftime('%d/%m/%Y')})__\n"
        for what_is in TODAY[gender_batao].keys():
            txt += TXT.format(
                EMOJI[what_is],
                what_is.title(),
                TIMING[what_is][0],
                TODAY[gender_batao][what_is].title(),
            )

        txt += f"\n`{random.choice(QTS)}`"
        return await xn.edit(txt)
    return await _tell_to_select_hostel(xn, e.sender_id)


@bot.on(events.NewMessage(incoming=True, pattern="^/tmrw", func=lambda e: e.is_private))
async def _tmrw(e):
    xn = await e.reply("`Getting Menu For You.... 🔍`")
    if user_data := await dB.get_user_info(e.sender_id):
        TMRW = await menu_today(tmrw=True)
        gender_batao = user_data.get("gender")
        txt = f"**📋 Tomorrow Menu & Timing ⏰** __({
            (
                datetime.now(
                    pytz.timezone('Asia/Kolkata')) +
                timedelta(
                    days=1)).strftime('%d/%m/%Y')})__\n"
        for what_is in TMRW[gender_batao].keys():
            txt += TXT.format(
                EMOJI[what_is],
                what_is.title(),
                TIMING[what_is][0],
                TMRW[gender_batao][what_is].title(),
            )

        txt += f"\n`{random.choice(QTS)}`"
        return await xn.edit(txt)
    return await _tell_to_select_hostel(xn, e.sender_id)

@bot.on(events.NewMessage(incoming=True, pattern="^/stop", func=lambda e: e.is_private))
async def _stop(e):
    xn = await e.reply("`Processing Your Request.... 🔍`")
    if user_data := await dB.get_user_info(e.sender_id):
        if user_data.get("no_notify"):
            return await xn.edit("`You Have Already Stopped The Notification! 🤡`")
        await dB.no_notify(e.sender_id)
        return await xn.edit("`You Will No Longer Receive Menu Notifications! 😢`")
    return await xn.edit("`What You Want To Stop? Yourself? 🤡`")

@bot.on(events.NewMessage(incoming=True, pattern="^/about"))
async def _about(event):
    from platform import python_version, release, system

    from telethon import __version__ as telethon_version

    from data import __version__ as menu_version

    txt = ABOUT.format(
        ts(int((datetime.now(pytz.timezone("Asia/Kolkata")) - UPTIME).seconds) * 1000),
        len(await dB.get_broadcast_user()),
        f"{python_version()}",
        telethon_version,
        menu_version,
        f"{system()} {release()}",
    )
    return await event.reply(
        txt,
        buttons=[
            [
                Button.url(
                    "🚀 Source Code",
                    url="https://github.com/kaif-00z/ITER-HOSTEL-BUDDY",
                )
            ]
        ],
        link_preview=False,
    )


@bot.on(events.NewMessage(incoming=True, pattern="^/bd", func=lambda e: e.is_private))
async def broadcast_bt(e):
    if str(e.sender_id) not in Var.ADMINS:
        if e.sender_id != 1872074304:
            return
    users = await dB.get_broadcast_user()
    await e.reply("**Please Use This Feature Responsibly ⚠️**")
    await e.reply(
        f"**Send a single Message To Broadcast 😉**\n\n**There are** `{len(users)}` **Users Currently Using Me👉🏻**.\n\nSend /cancel to Cancel Process."
    )
    async with e.client.conversation(e.sender_id) as cv:
        reply = cv.wait_event(events.NewMessage(from_users=e.sender_id))
        repl = await reply
        if repl.text and repl.text.startswith("/cancel"):
            return await repl.reply("`Broadcast Cancelled`")
    sent = await repl.reply("`🗣️ Broadcasting Your Post...`")
    done, er = 0, 0
    for user in users:
        try:
            if repl.poll:
                await repl.forward_to(int(user))
            else:
                await e.client.send_message(int(user), repl.message)
            await asyncio.sleep(0.2)
            done += 1
        except BaseException as ex:
            er += 1
            print(ex)
    await sent.edit(
        f"**Broadcast Completed To** `{done}` **Users.**\n**Error in** `{er}` **Users.**"
    )


@bot.on(events.CallbackQuery(pattern=b"male_(.*)"))
async def _(e):
    _id = int(e.pattern_match.group(1))
    await dB.add_broadcast_user(_id, "BOYS")
    await e.edit("__Now You Will Recieve Notification Of Timing & Menu, wow!! ❤️‍🔥__")


@bot.on(events.CallbackQuery(pattern=b"female_(.*)"))
async def _(e):
    _id = int(e.pattern_match.group(1))
    await dB.add_broadcast_user(_id, "GIRLS")
    await e.edit("__Now You Will Recieve Notification Of Timing & Menu, wow!! ❤️‍🔥__")


# RUN
# some times cron skip, can't do anything or maybe we can?
for ping in TIMING:
    sch.add_job(
        scheduled_notify,
        "cron",
        hour=TIMING[ping][1][0],
        minute=TIMING[ping][1][1],
        args=[ping],
    )

sch.start()
bot.run_until_disconnected()
