from telethon import TelegramClient, Button, events
from telethon.utils import get_display_name
from db import DataBase
from strings import TXT, EMOJI, QTS
from data.timing import TIMING
from decouple import config
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiofiles, asyncio, json, random

class Var:
    BOT_TOKEN = config("BOT_TOKEN")
    MONGO_SRV = config("MONGO_SRV")

bot = TelegramClient(
    None,
    api_id=6,
    api_hash="eb06d4abfb49dc3eeb1aeb98ae0f581e"
)
dB = DataBase(Var.MONGO_SRV)
sch = AsyncIOScheduler(timezone="Asia/Kolkata")

DATA = {
    "BOYS": {},
    "GIRLS": {}
}
TODAY = {
    "BOYS": {},
    "GIRLS": {}
}

async def start_bot() -> None: # ahh, no need of try , except cause program will crash in startup if something went wrong...

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

async def menu_today(): # no need of async, just i am too lazy to create one more scheduler with sync , so hehe
    for key in DATA.keys(): # better to copy the orginial DATA var as if we change something in loop it will give error, but here we aren't modifying anything , ye boiiiii
        TODAY[key] = DATA[key]["weeks"][(datetime.now().day // 7)]["days"][datetime.now().weekday()]

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
            TIMING[what_is],
            TODAY[key][what_is]
        )
        text = "\n\n".join(text.split("\n"))
        text += f"`{random.choice(QTS)}`"
        await broadcast(key, text)

@bot.on(events.NewMessage(incoming=True, pattern="^/start"))
async def _start(e):
    await e.reply(
        f"Hey `{get_display_name(e.sender)}`\nI Will Notify You With Menu and Timing Of **ITER HOSTELS MESS**\n\n__Please Select Your Gender Below 👇__\n\n**Made With ❤️‍🔥 By @kAiF_00z **\n\n__NOTE: ReSelecting Will Override The Previous Selection!!__",
        buttons=[
            [
                Button.inline("👨 BOYS HOSTEL", data=f"male_{e.sender_id}"),
                Button.inline("👩 GIRLS HOSTEL", data=f"female_{e.sender_id}"),
            ]
        ]
    )

@bot.on(events.NewMessage(incoming=True, pattern="^/today"))
async def _today(e):
    xn = await e.reply("`Getting Menu For You.... 🔍`")
    gender_batao = (await dB.get_user_info(e.sender_id)).get("gender")
    txt = "**📋 Todays Menu & Timing ⏰**\n"
    for what_is in TODAY[gender_batao].keys():
        txt += TXT.format(
            EMOJI[what_is],
            what_is.title(),
            TIMING[what_is],
            TODAY[gender_batao][what_is]
        )
    
    txt += f"\n`{random.choice(QTS)}`"
    await xn.edit(txt)

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

sch.add_job(menu_today, "interval", hours=1) # update menu in every 1 hour from static file (can use cron but lets see)


# better approach is to use for loop but its okay for now ig? in future will make it into a better algo and stuff but for now its good ig
sch.add_job(scheduled_notify, "cron", hour=7, minute=1, args=["BREAKFAST"])  # 7:01 AM IST
sch.add_job(scheduled_notify, "cron", hour=12, minute=1, args=["LUNCH"])  # 12:01 PM IST 
sch.add_job(scheduled_notify, "cron", hour=17, minute=1, args=["SNACKS"])  # 5:01 AM IST 
sch.add_job(scheduled_notify, "cron", hour=20, minute=1, args=["DINNER"])  # 8:01 AM IST 

sch.start()
bot.run_until_disconnected()