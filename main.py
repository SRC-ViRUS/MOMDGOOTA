import asyncio, os, datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetFullChatRequest

# بيانات الاتصال
api_id = 24087692
api_hash = '58bbe23b487e232699d93f1db818a98d'
session_string = "1ApWapzMBu0ivnheKrzAuzLihTMiNKMOurFuPNZJnqUpQxByZCzW3pqY9n1L3u2tXJ8oBValiSz8eaK_2M4MBSyLfIetg1SpTm665HNI2vcHWjHaIrWeVGsYYIxIbrnuw8k4vZBOtskw1Lb6lAbBwFfU7ankI3bHNNwZ5jrEhidlP2qi77A53r9m-SoZmoPCcXMNd9TvTLDImAGxslVEtSEQJbfFTnb0LTcGVOfYePGbywRlDQnmFF0uuCRG03iy4eMVjXVQLgW2b_OcfFoWZqLuGDMQIqKxvmWnpL_cpG5hETUGtzbZBjT1Z447_g7FsQQcUeVmEaVpuNY5WLYXqPRbQr-3UUAk="

client = TelegramClient(StringSession(session_string), api_id, api_hash)
os.makedirs("downloads", exist_ok=True)

# متغيرات
muted_private = set()
muted_groups = {}
previous_name = None
change_name_task = None  # مهمة تغيير الاسم التلقائي

# دالة للتحقق من صاحب البوت (مالك)
async def is_owner(event):
    me = await client.get_me()
    return event.sender_id == me.id

# --------- تغيير الاسم تلقائيًا كل دقيقة ---------
async def change_name_periodically():
    global previous_name
    me = await client.get_me()
    previous_name = me.first_name
    while True:
        now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)
        name = now.strftime('%I:%M')
        try:
            await client(UpdateProfileRequest(first_name=name))
        except Exception as e:
            print(f"خطأ بتغيير الاسم: {e}")
        await asyncio.sleep(60)

@client.on(events.NewMessage(pattern=r"\.اسم مؤقت"))
async def start_changing_name(event):
    global change_name_task
    if not await is_owner(event):
        return await event.reply("🚫 هذا الأمر خاص بالمالك فقط.")
    if change_name_task and not change_name_task.done():
        return await event.reply("🔄 تغيير الاسم التلقائي مفعل مسبقًا.")
    change_name_task = asyncio.create_task(change_name_periodically())
    await event.reply("✅ بدأ تغيير الاسم التلقائي كل دقيقة.")

@client.on(events.NewMessage(pattern=r"\.ايقاف الاسم"))
async def stop_changing_name(event):
    global change_name_task, previous_name
    if not await is_owner(event):
        return await event.reply("🚫 هذا الأمر خاص بالمالك فقط.")
    if change_name_task:
        change_name_task.cancel()
        change_name_task = None
    if previous_name:
        try:
            await client(UpdateProfileRequest(first_name=previous_name))
            await event.reply("🛑 تم إيقاف تغيير الاسم وإرجاع الاسم السابق.")
        except Exception as e:
            await event.reply(f"خطأ: {e}")
    else:
        await event.reply("❌ لا يوجد اسم سابق محفوظ.")

# --------- فحص ---------
@client.on(events.NewMessage(pattern=r"\.فحص"))
async def ping(event):
    if not await is_owner(event):
        return await event.reply("🚫 هذا الأمر خاص بالمالك فقط.")
    msg = await event.edit("✅ البوت شغال وبأفضل حال!")
    await client.send_message("me", "✨ حياتي الصعب، البوت شغال.")
    await asyncio.sleep(10)
    await msg.delete()

# --------- كشف معلومات القروب أو القناة ---------
@client.on(events.NewMessage(pattern=r"\.كشف"))
async def cmd_kashf(event):
    if not await is_owner(event):
        return await event.reply("🚫 هذا الأمر خاص بالمالك فقط.")
    chat = await event.get_chat()
    try:
        if getattr(chat, 'megagroup', False) or getattr(chat, 'broadcast', False):
            full = await client(GetFullChannelRequest(chat))
            title = full.chats[0].title
            id_ = full.chats[0].id
            members_count = full.full_chat.participants_count
            about = full.full_chat.about or "لا يوجد وصف"
        else:
            full = await client(GetFullChatRequest(chat))
            title = full.chats[0].title
            id_ = full.chats[0].id
            members_count = len(full.full_chat.participants)
            about = full.full_chat.about or "لا يوجد وصف"
    except:
        title = getattr(chat, 'title', '❌')
        id_ = getattr(chat, 'id', '❌')
        members_count = "❌"
        about = "❌"
    text = f"📊 معلومات:\n🔹 الاسم: {title}\n🔹 الايدي: `{id_}`\n🔹 عدد الأعضاء: {members_count}\n🔹 الوصف:\n{about}"
    await event.reply(text)

# --------- كتم / فك كتم ---------
@client.on(events.NewMessage(pattern=r"\.كتم$", func=lambda e: e.is_reply))
async def mute_user(event):
    if not await is_owner(event):
        return await event.reply("🚫 هذا الأمر خاص بالمالك فقط.")
    reply = await event.get_reply_message()
    if reply:
        uid, cid = reply.sender_id, event.chat_id
        (muted_private if event.is_private else muted_groups.setdefault(cid, set())).add(uid)
        msg = await event.edit("🔇 تم الكتم.")
        await asyncio.sleep(1)
        await msg.delete()

@client.on(events.NewMessage(pattern=r"\.الغاء الكتم$", func=lambda e: e.is_reply))
async def unmute_user(event):
    if not await is_owner(event):
        return await event.reply("🚫 هذا الأمر خاص بالمالك فقط.")
    reply = await event.get_reply_message()
    if reply:
        uid, cid = reply.sender_id, event.chat_id
        (muted_private if event.is_private else muted_groups.get(cid, set())).discard(uid)
        msg = await event.edit("🔊 تم فك الكتم.")
        await asyncio.sleep(1)
        await msg.delete()

@client.on(events.NewMessage(pattern=r"\.قائمة الكتم$"))
async def list_muted(event):
    if not await is_owner(event):
        return await event.reply("🚫 هذا الأمر خاص بالمالك فقط.")
    text = "📋 المكتومين:\n"
    for uid in muted_private:
        try:
            user = await client.get_entity(uid)
            text += f"🔸 خاص: {user.first_name}\n"
        except:
            continue
    for cid, users in muted_groups.items():
        if users:
            try:
                chat = await client.get_entity(cid)
                text += f"\n🔹 {chat.title}:\n"
                for uid in users:
                    try:
                        user = await client.get_entity(uid)
                        text += f" - {user.first_name}\n"
                    except:
                        continue
            except:
                continue
    await event.respond(text or "لا يوجد مكتومين.")

@client.on(events.NewMessage(pattern=r"\.مسح الكتم$"))
async def clear_mutes(event):
    if not await is_owner(event):
        return await event.reply("🚫 هذا الأمر خاص بالمالك فقط.")
    muted_private.clear()
    muted_groups.clear()
    msg = await event.edit("🗑️ تم مسح المكتومين.")
    await asyncio.sleep(1)
    await msg.delete()

# --------- حذف رسائل المكتومين وحفظ الوسائط ---------
@client.on(events.NewMessage(incoming=True))
async def handle_incoming(event):
    if (event.is_private and event.sender_id in muted_private) or \
       (event.chat_id in muted_groups and event.sender_id in muted_groups[event.chat_id]):
        return await event.delete()
    if event.is_private and event.media and getattr(event.media, 'ttl_seconds', None):
        try:
            path = await event.download_media("downloads/")
            await client.send_file("me", path, caption="📸 تم حفظ البصمة.")
            os.remove(path)
        except:
            pass

# --------- عرض الأوامر ---------
@client.on(events.NewMessage(pattern=r"\.اوامر"))
async def list_commands(event):
    if not await is_owner(event):
        return await event.reply("🚫 هذا الأمر خاص بالمالك فقط.")
    commands_text = (
        "🧠 قائمة أوامر البوت:\n\n"
        ".فحص - التحقق من أن البوت يعمل\n"
        ".كشف - عرض معلومات القروب أو القناة\n"
        ".كتم - كتم المستخدم (بالرد على رسالته)\n"
        ".الغاء الكتم - فك كتم المستخدم (بالرد على رسالته)\n"
        ".قائمة الكتم - عرض جميع المستخدمين المكتومين\n"
        ".مسح الكتم - إزالة جميع الكتم\n"
        ".اسم مؤقت - تشغيل تغيير الاسم التلقائي حسب الوقت (كل دقيقة)\n"
        ".ايقاف الاسم - إيقاف تغيير الاسم وإرجاع الاسم السابق\n"
    )
    await event.respond(commands_text)

# --------- تشغيل البوت ---------
async def main():
    await client.start()
    print("✅ البوت يعمل الآن.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
