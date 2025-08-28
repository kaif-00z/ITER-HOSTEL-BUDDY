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
import pytz
from datetime import datetime

import aiofiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from decouple import config
from telethon import Button, TelegramClient, events
from telethon.utils import get_display_name

from data.timing import TIMING
from db import DataBase
from strings import EMOJI, QTS, TXT


class Var:
    BOT_TOKEN = config("BOT_TOKEN")
    MONGO_SRV = config("MONGO_SRV")
    ADMINS = (config("ADMINS", default=",")).split(",")


bot = TelegramClient(None, api_id=6, api_hash="eb06d4abfb49dc3eeb1aeb98ae0f581e")
dB = DataBase(Var.MONGO_SRV)
sch = AsyncIOScheduler(timezone="Asia/Kolkata")

DATA = {"BOYS": {}, "GIRLS": {}}
TODAY = {"BOYS": {}, "GIRLS": {}}


# ahh, no need of try , except cause program will crash in startup if
# something went wrong...
async def start_bot() -> None:

    # too lazy to warp it into a function so emjoy
    print("Loading Static Menu Files....")
    async with aiofiles.open("data/W-BH 1-12.json", "r", encoding="utf-8") as f:
        DATA["BOYS"] = json.loads(await f.read())
    async with aiofiles.open("data/W-LH 1-4.json", "r", encoding="utf-8") as f:
        DATA["GIRLS"] = json.loads(await f.read())

    await menu_today()
    print("Successfully Loaded Static Menu Files!")

    await bot.start(bot_token=Var.BOT_TOKEN)
    bot.me = await bot.get_me()
    print(bot.me.username, "is Online Now.")


async def menu_today():  # no need of async, just i am too lazy to create one more scheduler with sync , so hehe
    for (
        key
    ) in (
        DATA.keys()
    ):  # better to copy the orginial DATA var as if we change something in loop it will give error, but here we aren't modifying anything , ye boiiiii
        dt = datetime.now(pytz.timezone("Asia/Kolkata"))
        TODAY[key] = DATA[key]["weeks"][(dt.day // 7) - 1]["days"][
            dt.now().weekday()
        ]
        print(f"Updated Menu For {key} at {dt}!!")


bot.loop.run_until_complete(start_bot())


async def broadcast(gen, txt):
    users = await dB.get_broadcast_user(gen)
    for user in users:
        try:
            await bot.send_message(int(user), txt)
            await asyncio.sleep(0.2)
        except BaseException as ex:
            print(ex)


async def scheduled_notify(what_is: str):
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
        f"Hey `{get_display_name(e.sender)}`\nI Will Notify You With Menu and Timing Of **ITER HOSTELS MESS**\n\n__Please Select Your Gender Below 👇__\n\n__NOTE: ReSelecting Will Override The Previous Selection!!\n\n__**Made With ❤️‍🔥 By @kAiF_00z **",
        buttons=[
            [
                Button.inline("👨 BOYS HOSTEL", data=f"male_{e.sender_id}"),
                Button.inline("👩 GIRLS HOSTEL", data=f"female_{e.sender_id}"),
            ]
        ],
    )


@bot.on(
    events.NewMessage(incoming=True, pattern="^/today", func=lambda e: e.is_private)
)
async def _today(e):
    xn = await e.reply("`Getting Menu For You.... 🔍`")
    gender_batao = (await dB.get_user_info(e.sender_id)).get("gender")
    txt = f"**📋 Today Menu & Timing ⏰** __({datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d/%m/%Y')})__\n"
    for what_is in TODAY[gender_batao].keys():
        txt += TXT.format(
            EMOJI[what_is],
            what_is.title(),
            TIMING[what_is][0],
            TODAY[gender_batao][what_is].title(),
        )

    txt += f"\n`{random.choice(QTS)}`"
    await xn.edit(txt)


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

# update menu in every 1 hour from static file (can use cron but lets see)
sch.add_job(menu_today, "interval", hours=1)

# some times cron skip, can't do anything or maybe can?
for ping in TIMING:
    sch.add_job(
        scheduled_notify, "cron", hour=TIMING[ping][1][0], minute=TIMING[ping][1][1], args=[ping]
    )

sch.start()
bot.run_until_disconnected()
