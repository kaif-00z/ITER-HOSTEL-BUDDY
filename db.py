#    This file is part of the AutoAnime distribution.
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
# https://github.com/kaif-00z/AutoAnimeBot/blob/main/LICENSE > .

# if you are using this following code then don't forgot to give proper
# credit to t.me/kAiF_00z (github.com/kaif-00z)

import sys
from traceback import format_exc

from motor.motor_asyncio import AsyncIOMotorClient

# no need of cache, coz its mongo :)
# maybe cache will be added in future idk


class DataBase:
    def __init__(self, mongo_srv):
        try:
            print("Trying To Connect With MongoDB")
            self.client = AsyncIOMotorClient(mongo_srv)
            self.user_info_db = self.client["ITER"]["userInfo"]
            print("Successfully Connected With MongoDB")
        except Exception as error:
            print(format_exc())
            print(str(error))
            sys.exit(1)

    async def add_broadcast_user(self, user_id, gender):
        # don't ask why not using insert_one, get some brain bro
        await self.user_info_db.update_one(
            {"_id": user_id},
            {"$set": {"gender": gender, "no_notify": False}},
            upsert=True,
        )

    async def get_user_info(self, user_id):
        data = await self.user_info_db.find_one({"_id": user_id})
        return data or {}

    async def get_broadcast_user(self):
        data = self.user_info_db.find()
        return [i["_id"] for i in (await data.to_list(length=None))]

    # make no sense to declare "gender" as optional arg, but who cares?
    async def get_menu_notify_user(self, gender=None):
        data = (
            self.user_info_db.find({"gender": gender, "no_notify": False})
            if gender
            else self.user_info_db.find({"no_notify": False})
        )
        return [i["_id"] for i in (await data.to_list(length=None))]

    async def no_notify(self, user_id):
        await self.user_info_db.update_one(
            {"_id": user_id}, {"$set": {"no_notify": True}}, upsert=True
        )
