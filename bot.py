from dotenv import load_dotenv
load_dotenv(
    "config.env",
    override=True,
)
import asyncio
import os
import time
import shutil, psutil
from PIL import Image
from pyrogram import Client, filters
from pyrogram.errors import (
    FloodWait,
    InputUserDeactivated,
    UserIsBlocked,
    PeerIdInvalid,
)
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    User
)
from pyromod import listen

from config import Config
from helpers import database
from __init__ import (
    AUDIO_EXTENSIONS,
    BROADCAST_MSG,
    LOGGER,
    MERGE_MODE,
    SUBTITLE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    gDict,
    UPLOAD_AS_DOC,
    UPLOAD_TO_DRIVE,
    queueDB,
    formatDB,
    replyDB,
    bMaker,
)
from helpers.utils import get_readable_time, get_readable_file_size


botStartTime = time.time()

class MergeBot(Client):
    def start(self):
        super().start()
        try:
            self.send_message(chat_id=int(Config.OWNER), text="<b>Bot Started!</b>")
        except Exception as err:
            LOGGER.error("𝐁𝐨𝐨𝐭 𝐚𝐥𝐞𝐫𝐭 𝐟𝐚𝐢𝐥𝐞𝐝! 𝐏𝐥𝐞𝐚𝐬𝐞 𝐬𝐭𝐚𝐫𝐭 𝐛𝐨𝐭 𝐢𝐧 𝐏𝐌")
        return LOGGER.info("Bot Started!")

    def stop(self):
        super().stop()
        return LOGGER.info("Bot Stopped")

mergeApp = MergeBot(
    name="merge-bot",
    api_hash=Config.API_HASH,
    api_id=int(Config.TELEGRAM_API),
    bot_token=Config.BOT_TOKEN,
    workers=300,
    plugins=dict(root="plugins"),
    app_version="4.0+yash-multiMergeSupport",
)


if os.path.exists("./downloads") == False:
    os.makedirs("./downloads")

@mergeApp.on_message(filters.command(['log']) & filters.user(Config.OWNER_USERNAME))
async def sendLogFile(c:Client,m:Message):
    await m.reply_document(document="./mergebotlog.txt")
    return

@mergeApp.on_message(filters.command(["login"]) & filters.private)
async def allowUser(c: Client, m: Message):
    if await database.allowedUser(uid=m.from_user.id) is True | m.from_user.id == int(Config.OWNER):
        await m.reply_text(text=f"**Dont Spam**\n  ⚡ 𝐍𝐨𝐰 𝐲𝐨𝐮 𝐜𝐚𝐧 𝐮𝐬𝐞 𝐦𝐞!!", quote=True)
    else:
        passwd = m.text.split(" ", 1)[1]
        passwd = passwd.strip()
        if passwd == Config.PASSWORD:
            await database.allowUser(
                uid=m.from_user.id,
                fname=m.from_user.first_name,
                lname=m.from_user.last_name,
            )
            await m.reply_text(
                text=f"**Login passed ✅,**\n  ⚡ 𝐍𝐨𝐰 𝐲𝐨𝐮 𝐜𝐚𝐧 𝐮𝐬𝐞 𝐦𝐞!!", quote=True
            )
        else:
            await m.reply_text(
                text=f"**Login failed ❌,**\n  🛡️ ᴜɴꜰᴏʀᴛᴜɴᴀᴛᴇʟʏ ʏᴏᴜ ᴄᴀɴ'ᴛ ᴜꜱᴇ ᴍᴇ\n\n**𝐂𝐨𝐧𝐭𝐚𝐜𝐭: 🈲 @{Config.OWNER_USERNAME}",
                quote=True,
            )
    return


@mergeApp.on_message(
    filters.command(["stats"]) & filters.private & filters.user(Config.OWNER)
)
async def stats_handler(c: Client, m: Message):
    currentTime = get_readable_time(time.time() - botStartTime)
    total, used, free = shutil.disk_usage(".")
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    stats = (
        f"<b>「 💠 BOT STATISTICS 」</b>\n"
        f"<b></b>\n"
        f"<b>⏳ Bot Uptime : {currentTime}</b>\n"
        f"<b>💾 Total Disk Space : {total}</b>\n"
        f"<b>📀 Total Used Space : {used}</b>\n"
        f"<b>💿 Total Free Space : {free}</b>\n"
        f"<b>🔺 Total Upload : {sent}</b>\n"
        f"<b>🔻 Total Download : {recv}</b>\n"
        f"<b>🖥 CPU : {cpuUsage}%</b>\n"
        f"<b>⚙️ RAM : {memory}%</b>\n"
        f"<b>💿 DISK : {disk}%</b>"
    )
    await m.reply_text(text=stats, quote=True)


@mergeApp.on_message(
    filters.command(["broadcast"]) & filters.private & filters.user(Config.OWNER)
)
async def broadcast_handler(c: Client, m: Message):
    msg = m.reply_to_message
    userList = await database.broadcast()
    len = userList.collection.count_documents({})
    status = await m.reply_text(text=BROADCAST_MSG.format(str(len), "0"), quote=True)
    success = 0
    for i in range(len):
        try:
            await msg.copy(chat_id=userList[i]["_id"])
            success = i + 1
            await status.edit_text(text=BROADCAST_MSG.format(len, success))
            LOGGER.info(f"Message sent to {userList[i]['name']} ")
        except FloodWait as e:
            await asyncio.sleep(e.x)
            await msg.copy(chat_id=userList[i]["_id"])
            LOGGER.info(f"Message sent to {userList[i]['name']} ")
        except InputUserDeactivated:
            await database.deleteUser(userList[i]["_id"])
            LOGGER.info(f"{userList[i]['_id']} - {userList[i]['name']} : deactivated\n")
        except UserIsBlocked:
            await database.deleteUser(userList[i]["_id"])
            LOGGER.info(
                f"{userList[i]['_id']} - {userList[i]['name']} : blocked the bot\n"
            )
        except PeerIdInvalid:
            await database.deleteUser(userList[i]["_id"])
            LOGGER.info(
                f"{userList[i]['_id']} - {userList[i]['name']} : user id invalid\n"
            )
        except Exception as err:
            LOGGER.warning(f"{err}\n")
        await asyncio.sleep(3)
    await status.edit_text(
        text=BROADCAST_MSG.format(len, success)
        + f"**Failed: {str(len-success)}**\n\n__🤓 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐂𝐨𝐦𝐩𝐥𝐞𝐭𝐞𝐝 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲__",
    )


@mergeApp.on_message(filters.command(["start"]) & filters.private)
async def start_handler(c: Client, m: Message):
    if m.from_user.id != int(Config.OWNER):
        await database.addUser(
            uid=m.from_user.id,
            fname=m.from_user.first_name,
            lname=m.from_user.last_name,
        )
        if await database.allowedUser(uid=m.from_user.id) is False:
            res = await m.reply_text(
                text=f"Hi **{m.from_user.first_name}**\n\n 🛡️ ᴜɴꜰᴏʀᴛᴜɴᴀᴛᴇʟʏ ʏᴏᴜ ᴄᴀɴ'ᴛ ᴜꜱᴇ ᴍᴇ\n\n**𝐂𝐨𝐧𝐭𝐚𝐜𝐭: 🈲 @{Config.OWNER_USERNAME}** ",
                quote=True,
            )
            return
    res = await m.reply_text(
        text=f"Hi **{m.from_user.first_name}**\n\n ⚡𝐇𝐢𝐞𝐞 𝐈 𝐀𝐦 𝐀 𝐅𝐢𝐥𝐞/𝐕𝐢𝐝𝐞𝐨 𝐌𝐞𝐫𝐠𝐞𝐫 𝐁𝐨𝐭\n\n😎 𝐈 𝐂𝐚𝐧 𝐌𝐞𝐫𝐠𝐞 𝐓𝐞𝐥𝐞𝐠𝐫𝐚𝐦 𝐅𝐢𝐥𝐞𝐬!, 𝐀𝐧𝐝 𝐔𝐩𝐥𝐨𝐚𝐝 𝐈𝐭 𝐓𝐨 𝐓𝐞𝐥𝐞𝐠𝐫𝐚𝐦\n\n**Owner: 🈲 @{Config.OWNER_USERNAME}** ",
        quote=True,
    )


@mergeApp.on_message((filters.document | filters.video | filters.audio) & filters.private)
async def files_handler(c: Client, m: Message):
    user_id = m.from_user.id
    if user_id != int(Config.OWNER):
        if await database.allowedUser(uid=user_id) is False:
            res = await m.reply_text(
                text=f"Hi **{m.from_user.first_name}**\n\n 🛡️ ᴜɴꜰᴏʀᴛᴜɴᴀᴛᴇʟʏ ʏᴏᴜ ᴄᴀɴ'ᴛ ᴜꜱᴇ ᴍᴇ\n\n**𝐂𝐨𝐧𝐭𝐚𝐜𝐭: 🈲 @{Config.OWNER_USERNAME}** ",
                quote=True,
            )
            return
    input_ = f"downloads/{str(user_id)}/input.txt"
    if os.path.exists(input_):
        await m.reply_text("ꜱᴏʀʀʏ ʙʀᴏ,\nᴀʟʀᴇᴀᴅʏ ᴏɴᴇ ᴘʀᴏᴄᴇꜱꜱ ɪɴ ᴘʀᴏɢʀᴇꜱꜱ!\nᴅᴏɴ'ᴛ ꜱᴘᴀᴍ.")
        return
    media = m.video or m.document or m.audio
    if media.file_name is None:
        await m.reply_text("File Not Found")
        return
    currentFileNameExt = media.file_name.rsplit(sep=".")[-1].lower()
    if currentFileNameExt in "conf":
        await m.reply_text(
            text="**💾 ᴄᴏɴꜰɪɢ ꜰɪʟᴇ ꜰᴏᴜɴᴅ, ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ꜱᴀᴠᴇ ɪᴛ?**",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✅ ʏᴇꜱ", callback_data=f"rclone_save"),
                        InlineKeyboardButton("❌ ɴᴏ", callback_data="rclone_discard"),
                    ]
                ]
            ),
            quote=True,
        )
        return
    if MERGE_MODE.get(user_id) is None:
        userMergeMode = database.getUserMergeMode(user_id)
        if userMergeMode is not None:
            MERGE_MODE[user_id] = userMergeMode
        else:
            database.setUserMergeMode(uid=user_id, mode=1)
            MERGE_MODE[user_id] = 1

    if MERGE_MODE[user_id] == 1:

        if queueDB.get(user_id, None) is None:
            formatDB.update({user_id: currentFileNameExt})
        if formatDB.get(
            user_id, None
        ) is not None and currentFileNameExt != formatDB.get(user_id):
            await m.reply_text(
                f"ꜰɪʀꜱᴛ ʏᴏᴜ ꜱᴇɴᴛ ᴀ {formatDB.get(user_id).upper()} ꜰɪʟᴇ ꜱᴏ ɴᴏᴡ ꜱᴇɴᴅ ᴏɴʟʏ ᴛʜᴀᴛ ᴛʏᴘᴇ ᴏꜰ ꜰɪʟᴇ.",
                quote=True,
            )
            return
        if currentFileNameExt not in VIDEO_EXTENSIONS:
            await m.reply_text(
                "ᴛʜɪꜱ ᴠɪᴅᴇᴏ ꜰᴏʀᴍᴀᴛ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ!\nᴏɴʟʏ ꜱᴇɴᴅ ᴍᴘ4 ᴏʀ ᴍᴋᴠ ᴏʀ ᴡᴇʙᴍ.",
                quote=True,
            )
            return
        editable = await m.reply_text("Please Wait ...", quote=True)
        MessageText = "ᴏᴋᴀʏ,\nɴᴏᴡ ꜱᴇɴᴅ ᴍᴇ ɴᴇxᴛ ᴠɪᴅᴇᴏ ᴏʀ ᴘʀᴇꜱꜱ *𝐌𝐞𝐫𝐠𝐞 𝐍𝐨𝐰** ʙᴜᴛᴛᴏɴ!"

        if queueDB.get(user_id, None) is None:
            queueDB.update({user_id: {"videos": [], "subtitles": [], "audios":[]}})
        if (
            len(queueDB.get(user_id)["videos"]) >= 0
            and len(queueDB.get(user_id)["videos"]) < 10
        ):
            queueDB.get(user_id)["videos"].append(m.id)
            queueDB.get(m.from_user.id)["subtitles"].append(None)

            # LOGGER.info(
            #     queueDB.get(user_id)["videos"], queueDB.get(m.from_user.id)["subtitles"]
            # )

            if len(queueDB.get(user_id)["videos"]) == 1:
                reply_ = await editable.edit(
                    "**ꜱᴇɴᴅ ᴍᴇ ꜱᴏᴍᴇ ᴍᴏʀᴇ ᴠɪᴅᴇᴏꜱ ᴛᴏ ᴍᴇʀɢᴇ ᴛʜᴇᴍ ɪɴᴛᴏ ꜱɪɴɢʟᴇ ꜰɪʟᴇ**",
                    reply_markup=InlineKeyboardMarkup(
                        bMaker.makebuttons(["Cancel"], ["cancel"])
                    ),
                )
                replyDB.update({user_id: reply_.id})
                return
            if queueDB.get(user_id, None)["videos"] is None:
                formatDB.update({user_id: currentFileNameExt})
            if replyDB.get(user_id, None) is not None:
                await c.delete_messages(
                    chat_id=m.chat.id, message_ids=replyDB.get(user_id)
                )
            if len(queueDB.get(user_id)["videos"]) == 10:
                MessageText = "ᴏᴋᴀʏ, ɴᴏᴡ ᴊᴜꜱᴛ ᴘʀᴇꜱꜱ **𝐌𝐞𝐫𝐠𝐞 𝐍𝐨𝐰** ʙᴜᴛᴛᴏɴ ᴘʟᴏx!"
            markup = await makeButtons(c, m, queueDB)
            reply_ = await editable.edit(
                text=MessageText, reply_markup=InlineKeyboardMarkup(markup)
            )
            replyDB.update({user_id: reply_.id})
        elif len(queueDB.get(user_id)["videos"]) > 10:
            markup = await makeButtons(c, m, queueDB)
            await editable.text(
                "Max 10 videos allowed", reply_markup=InlineKeyboardMarkup(markup)
            )

    elif MERGE_MODE[user_id] == 2:
        editable = await m.reply_text("Please Wait ...", quote=True)
        MessageText = (
            "ᴏᴋᴀʏ,\nɴᴏᴡ ꜱᴇɴᴅ ᴍᴇ ꜱᴏᴍᴇ ᴍᴏʀᴇ <u>Audios</u> ᴏʀ ᴘʀᴇꜱꜱ **𝐌𝐞𝐫𝐠𝐞 𝐍𝐨𝐰** ʙᴜᴛᴛᴏɴ!"
        )

        if queueDB.get(user_id, None) is None:
            queueDB.update({user_id: {"videos": [], "subtitles": [], "audios":[]}})
        if len(queueDB.get(user_id)["videos"]) == 0:
            queueDB.get(user_id)["videos"].append(m.id)
            # if len(queueDB.get(user_id)["videos"])==1:
            reply_ = await editable.edit(
                text="Now, Send all the audios you want to merge",
                reply_markup=InlineKeyboardMarkup(
                    bMaker.makebuttons(["Cancel"], ["cancel"])
                ),
            )
            replyDB.update({user_id: reply_.id})
            return
        elif (
            len(queueDB.get(user_id)["videos"]) >= 1
            and currentFileNameExt in AUDIO_EXTENSIONS
        ):
            queueDB.get(user_id)["audios"].append(m.id)
            if replyDB.get(user_id, None) is not None:
                await c.delete_messages(
                    chat_id=m.chat.id, message_ids=replyDB.get(user_id)
                )
            markup = await makeButtons(c, m, queueDB)

            reply_ = await editable.edit(
                text=MessageText, reply_markup=InlineKeyboardMarkup(markup)
            )
            replyDB.update({user_id: reply_.id})
        else:
            await m.reply("ᴛʜɪꜱ ꜰɪʟᴇᴛʏᴘᴇ ɪꜱ ɴᴏᴛ ᴠᴀʟɪᴅ")
            return

    elif MERGE_MODE[user_id] == 3:

        editable = await m.reply_text("Please Wait ...", quote=True)
        MessageText = "Okay,\nNow Send Me Some More <u>Subtitles</u> or Press **Merge Now** Button!"
        if queueDB.get(user_id, None) is None:
            queueDB.update({user_id: {"videos": [], "subtitles": [], "audios":[]}})
        if len(queueDB.get(user_id)["videos"]) == 0:
            queueDB.get(user_id)["videos"].append(m.id)
            # if len(queueDB.get(user_id)["videos"])==1:
            reply_ = await editable.edit(
                text="ɴᴏᴡ, ꜱᴇɴᴅ ᴀʟʟ ᴛʜᴇ ꜱᴜʙᴛɪᴛʟᴇꜱ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴍᴇʀɢᴇ",
                reply_markup=InlineKeyboardMarkup(
                    bMaker.makebuttons(["Cancel"], ["cancel"])
                ),
            )
            replyDB.update({user_id: reply_.id})
            return
        elif (
            len(queueDB.get(user_id)["videos"]) >= 1
            and currentFileNameExt in SUBTITLE_EXTENSIONS
        ):
            queueDB.get(user_id)["subtitles"].append(m.id)
            if replyDB.get(user_id, None) is not None:
                await c.delete_messages(
                    chat_id=m.chat.id, message_ids=replyDB.get(user_id)
                )
            markup = await makeButtons(c, m, queueDB)

            reply_ = await editable.edit(
                text=MessageText, reply_markup=InlineKeyboardMarkup(markup)
            )
            replyDB.update({user_id: reply_.id})
        else:
            await m.reply("ᴛʜɪꜱ ꜰɪʟᴇ ᴛʏᴘᴇ ɪꜱ ɴᴏᴛ ᴠᴀʟɪᴅ")
            return


@mergeApp.on_message(filters.photo & filters.private)
async def photo_handler(c: Client, m: Message):
    if m.from_user.id != int(Config.OWNER):
        if await database.allowedUser(uid=m.from_user.id) is False:
            res = await m.reply_text(
                text=f"Hi **{m.from_user.first_name}**\n\n 🛡️ 𝐔𝐧𝐟𝐨𝐫𝐭𝐮𝐧𝐚𝐭𝐞𝐥𝐲 𝐘𝐨𝐮 𝐂𝐚𝐧'𝐭 𝐔𝐬𝐞 𝐌𝐞\n\n**Contact: 🈲 @{Config.OWNER_USERNAME}** ",
                quote=True,
            )
            return
    thumbnail = m.photo.file_id
    msg = await m.reply_text("ꜱᴀᴠɪɴɢ ᴛʜᴜᴍʙɴᴀɪʟ. . . .", quote=True)
    await database.saveThumb(m.from_user.id, thumbnail)
    LOCATION = f"./downloads/{m.from_user.id}_thumb.jpg"
    await c.download_media(message=m, file_name=LOCATION)
    await msg.edit_text(text="✅ ᴄᴜꜱᴛᴏᴍ ᴛʜᴜᴍʙɴᴀɪʟ ꜱᴀᴠᴇᴅ!")


@mergeApp.on_message(filters.command(["help"]) & filters.private)
async def help_msg(c: Client, m: Message):
    await m.reply_text(
        text="""**𝐅𝐨𝐥𝐥𝐨𝐰 𝐓𝐡𝐞𝐬𝐞 𝐒𝐭𝐞𝐩𝐬:

1) ꜱᴇɴᴅ ᴍᴇ ᴛʜᴇ ᴄᴜꜱᴛᴏᴍ ᴛʜᴜᴍʙɴᴀɪʟ (ᴏᴘᴛɪᴏɴᴀʟ).
2) ꜱᴇɴᴅ ᴛᴡᴏ ᴏʀ ᴍᴏʀᴇ ʏᴏᴜʀ ᴠɪᴅᴇᴏꜱ ᴡʜɪᴄʜ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴍᴇʀɢᴇ
3) ᴀꜰᴛᴇʀ ꜱᴇɴᴅɪɴɢ ᴀʟʟ ꜰɪʟᴇꜱ ꜱᴇʟᴇᴄᴛ ᴍᴇʀɢᴇ ᴏᴘᴛɪᴏɴꜱ
4) ꜱᴇʟᴇᴄᴛ ᴛʜᴇ ᴜᴘʟᴏᴀᴅ ᴍᴏᴅᴇ.
5) ꜱᴇʟᴇᴄᴛ ʀᴇɴᴀᴍᴇ ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ɢɪᴠᴇ ᴄᴜꜱᴛᴏᴍ ꜰɪʟᴇ ɴᴀᴍᴇ ᴇʟꜱᴇ ᴘʀᴇꜱꜱ ᴅᴇꜰᴀᴜʟᴛ**""",
        quote=True,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("ᴄʟᴏꜱᴇ 🔐", callback_data="close")]]
        ),
    )


@mergeApp.on_message(filters.command(["about"]) & filters.private)
async def about_handler(c: Client, m: Message):
    await m.reply_text(
        text="""
**WHAT'S NEW:**
+ Upload to drive using your own rclone config
+ Merged video preserves all streams of the first video you send (i.e. all audiotracks/subtitles)
**FEATURES:**
+ Merge Upto 10 videos in one
+ Upload as document/video
+ Custom thumbnail support
+ Users can login to bot using password
+ Owner can broadcast message to all users
		""",
        quote=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Developer", url="https://t.me/Yuvi_4502")],
                [
                    InlineKeyboardButton(
                        "Source Code", url="https://github.com/FilmyFather/Merger-Bot"
                    ),
                    InlineKeyboardButton(
                        "Deployed By 𝝲𝞄𝙫𝝘𝛂𝐉", url=f"https://t.me/{Config.OWNER_USERNAME}"
                    ),
                ],
                [InlineKeyboardButton("ᴄʟᴏꜱᴇ 🔐", callback_data="close")],
            ]
        ),
    )


@mergeApp.on_message(filters.command(["showthumbnail"]) & filters.private)
async def show_thumbnail(c: Client, m: Message):
    try:
        thumb_id = await database.getThumb(m.from_user.id)
        LOCATION = f"./downloads/{m.from_user.id}_thumb.jpg"
        await c.download_media(message=str(thumb_id), file_name=LOCATION)
        if os.path.exists(LOCATION) is False:
            await m.reply_text(text="❌ ᴄᴜꜱᴛᴏᴍ ᴛʜᴜᴍʙɴᴀɪʟ ɴᴏᴛ ꜰᴏᴜɴᴅ!", quote=True)
        else:
            await m.reply_photo(
                photo=LOCATION, caption="🖼️ ʏᴏᴜʀ ᴄᴜꜱᴛᴏᴍ ᴛʜᴜᴍʙɴᴀɪʟ✔", quote=True
            )
    except Exception as err:
        await m.reply_text(text="❌ ᴄᴜꜱᴛᴏᴍ ᴛʜᴜᴍʙɴᴀɪʟ ɴᴏᴛ ꜰᴏᴜɴᴅ!", quote=True)


@mergeApp.on_message(filters.command(["deletethumbnail"]) & filters.private)
async def delete_thumbnail(c: Client, m: Message):
    try:
        await database.delThumb(m.from_user.id)
        if os.path.exists(f"downloads/{str(m.from_user.id)}"):
            os.remove(f"downloads/{str(m.from_user.id)}")
        await m.reply_text("✅ ᴅᴇʟᴇᴛᴇᴅ ꜱᴜᴄᴇꜱꜱꜰᴜʟʟʏ ✔", quote=True)
    except Exception as err:
        await m.reply_text(text="❌ ᴄᴜꜱᴛᴏᴍ ᴛʜᴜᴍʙɴᴀɪʟ ɴᴏᴛ ꜰᴏᴜɴᴅ!", quote=True)


async def showQueue(c: Client, cb: CallbackQuery):
    try:
        markup = await makeButtons(c, cb.message, queueDB)
        await cb.message.edit(
            text="Okay,\nNow Send Me Next Video or Press **Merge Now** Button!",
            reply_markup=InlineKeyboardMarkup(markup),
        )
    except ValueError:
        await cb.message.edit("Send Some more videos")
    return


async def delete_all(root):
    try:
        shutil.rmtree(root)
    except Exception as e:
        LOGGER.info(e)


async def makeButtons(bot: Client, m: Message, db: dict):
    markup = []

    if MERGE_MODE[m.chat.id] == 1:
        for i in await bot.get_messages(
            chat_id=m.chat.id, message_ids=db.get(m.chat.id)["videos"]
        ):
            media = i.video or i.document or None
            if media is None:
                continue
            else:
                markup.append(
                    [
                        InlineKeyboardButton(
                            f"{media.file_name}",
                            callback_data=f"showFileName_{i.id}",
                        )
                    ]
                )

    elif MERGE_MODE[m.chat.id] == 2:
        msgs: list[Message] = await bot.get_messages(
            chat_id=m.chat.id, message_ids=db.get(m.chat.id)["audios"]
        )
        msgs.insert(
            0,
            await bot.get_messages(
                chat_id=m.chat.id, message_ids=db.get(m.chat.id)["videos"][0]
            ),
        )
        for i in msgs:
            media = i.audio or i.document or None
            if media is None:
                continue
            else:
                markup.append(
                    [
                        InlineKeyboardButton(
                            f"{media.file_name}",
                            callback_data=f"showFileName_{i.id}",
                        )
                    ]
                )

    elif MERGE_MODE[m.chat.id] == 3:
        msgs: list[Message] = await bot.get_messages(
            chat_id=m.chat.id, message_ids=db.get(m.chat.id)["subtitles"]
        )
        msgs.insert(
            0,
            await bot.get_messages(
                chat_id=m.chat.id, message_ids=db.get(m.chat.id)["videos"][0]
            ),
        )
        for i in msgs:
            media = i.video or i.document or None

            if media is None:
                continue
            else:
                markup.append(
                    [
                        InlineKeyboardButton(
                            f"{media.file_name}",
                            callback_data=f"showFileName_{i.id}",
                        )
                    ]
                )

    markup.append([InlineKeyboardButton("🔗 ᴍᴇʀɢᴇ ɴᴏᴡ", callback_data="merge")])
    markup.append([InlineKeyboardButton("💥 ᴄʟᴇᴀʀ ꜰɪʟᴇꜱ", callback_data="cancel")])
    return markup

LOGCHANNEL = Config.LOGCHANNEL
try:
    if Config.USER_SESSION_STRING is None:
        raise KeyError
    LOGGER.info("Starting USER Session")
    userBot = Client(
        name="merge-bot-user",
        session_string=Config.USER_SESSION_STRING,
        no_updates=True
    )
    
except KeyError:
    userBot = None
    LOGGER.warning("No User Session, Default Bot session will be used")


if __name__ == "__main__":
    # with mergeApp:
    #     bot:User = mergeApp.get_me()
    #     bot_username = bot.username
    try:
        with userBot:
            userBot.send_message(chat_id=int(LOGCHANNEL), text="Bot booted with Premium Account,\n\n  Thanks for using <a href='https://github.com/FilmyFather/Merger-bot'>this repo</a>",disable_web_page_preview=True)
            user = userBot.get_me()
            Config.IS_PREMIUM = user.is_premium
    except Exception as err:
        LOGGER.error(f"{err}")
        Config.IS_PREMIUM = False
        pass

    mergeApp.run()
