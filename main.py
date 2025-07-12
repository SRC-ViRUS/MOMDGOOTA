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
session_string = "1ApWapzMBuxTL1qnTZUK7UqvewYm0Tt61id0K4qsYkrB853FfDGuqFVzImvMrx-w_6frK50fgV-bLcVrPvZEme7d_Jl3FvV562HPMv9majShXEpi9IoONZZ2yW2BHBx7Glv1YIwTLuG1olGITS7GQGV1fVPnhOTAld8aLvIA1m_BoBL8dFPo3TaZKM0Fm2baBXTtEW7qGeFWKj2N6dNXvj7vXqcBXYnH7ZtSGSphSZJfQQtM1NQMnkC2_bZaxu7ImqRyJVWhPBuPbRPDU4QmT9MCRaKYxwUt6N-AkoXKu3hOh4du5JnnLHW4a_nwzSuvWNlzB03HykDrgaJf1quAxGLyDUpys9Ek=" 

client = TelegramClient(StringSession(session_string), api_id, api_hash)
os.makedirs("downloads", exist_ok=True)

# متغيرات
muted_private = set()
muted_groups = {}
previous_name = None

# --------- تغيير الاسم مؤقتاً ---------
@client.on(events.NewMessage(pattern=r"\.اسم مؤقت"))
async def change_name_once(event):
    global previous_name
    try:
        me = await client.get_me()
        previous_name = me.first_name
        now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)
        name = now.strftime('%I:%M')
        await client(UpdateProfileRequest(first_name=name))
        msg = await event.edit(f"✅ تم تغيير الاسم مؤقتًا إلى: {name}")
        await asyncio.sleep(1)
        await msg.delete()
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds)
    except Exception as err:
        await event.reply(f"خطأ: {err}")

@client.on(events.NewMessage(pattern=r"\.ايقاف الاسم"))
async def revert_name(event):
    global previous_name
    if previous_name:
        try:
            await client(UpdateProfileRequest(first_name=previous_name))
            msg = await event.edit("🛑 تم إرجاع الاسم السابق.")
            await asyncio.sleep(1)
            await msg.delete()
        except Exception as e:
            await event.reply(f"خطأ: {e}")
    else:
        await event.reply("❌ لا يوجد اسم محفوظ لإرجاعه.")

# --------- فحص ---------
@client.on(events.NewMessage(pattern=r"\.فحص"))
async def ping(event):
    msg = await event.edit("✅ البوت شغال وبأفضل حال!")
    await client.send_message("me", "✨ حياتي الصعب، البوت شغال.")
    await asyncio.sleep(10)
    await msg.delete()

# --------- كشف معلومات القروب أو القناة ---------
@client.on(events.NewMessage(pattern=r"\.كشف"))
async def cmd_kashf(event):
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
    reply = await event.get_reply_message()
    if reply:
        uid, cid = reply.sender_id, event.chat_id
        (muted_private if event.is_private else muted_groups.setdefault(cid, set())).add(uid)
        msg = await event.edit("🔇 تم الكتم.")
        await asyncio.sleep(1)
        await msg.delete()

@client.on(events.NewMessage(pattern=r"\.الغاء الكتم$", func=lambda e: e.is_reply))
async def unmute_user(event):
    reply = await event.get_reply_message()
    if reply:
        uid, cid = reply.sender_id, event.chat_id
        (muted_private if event.is_private else muted_groups.get(cid, set())).discard(uid)
        msg = await event.edit("🔊 تم فك الكتم.")
        await asyncio.sleep(1)
        await msg.delete()

@client.on(events.NewMessage(pattern=r"\.قائمة الكتم$"))
async def list_muted(event):
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
    await event.respond("🧠 أوامر البوت:\n.فحص\n.كشف\n.كتم\n.الغاء الكتم\n.اسم مؤقت\n.ايقاف الاسم\n.قائمة الكتم\n.مسح الكتم")

# --------- تشغيل البوت ---------
async def main():
    await client.start()
    print("✅ البوت يعمل الآن.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
