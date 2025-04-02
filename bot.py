import asyncio
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipant

# Bot Configuration
API_ID = '21259513'
API_HASH = '29e43fc190ebaef2ee94542cafb0614d'
BOT_TOKEN = '7415801305:AAHlUOoQHzuTLURS-ba2oWKPvRQiyogpJzk'
CHANNEL_USERNAME = 'offchats'  # Replace with your channel username
ADMIN_USERNAME = 'seiao'  # Replace with your admin's username (without @)
ADMIN_ID = 6076683960  # Replace with your admin's Telegram ID

# Initialize bot
bot = TelegramClient('new_report_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Global Variables
user_reporting = {}
notified_users = set()
active_users = set()
broadcasting = False
waiting_for_broadcast_message = None
broadcast_message_content = None

# Helper Function: Check Channel Membership
async def is_user_in_channel(user_id):
    try:
        participant = await bot(GetParticipantRequest(CHANNEL_USERNAME, user_id))
        return isinstance(participant.participant, ChannelParticipant)
    except:
        return False

# Start Command: Force Join + Notify Admin
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    user = await bot.get_entity(user_id)
    username = user.username or "No Username"
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    permanent_link = f"tg://user?id={user_id}"

    # Add user to active users list
    active_users.add(user_id)

    # Check if user is in the channel
    if not await is_user_in_channel(user_id):
        await event.reply(
            f"👋🏻** Hey {full_name}! You must join our channel to use this bot.**",
            buttons=[Button.url("offchats", f"https://t.me/{CHANNEL_USERNAME}"),
Button.url("Python-Botz", "https://t.me/+WPKg3Ci2sMBkMDc1")]
        )
        return

    # Notify Admin Once
    if user_id not in notified_users:
        notified_users.add(user_id)
        total_users = len(active_users)
        await bot.send_message(
            ADMIN_USERNAME,
            f"🔔 **New User Alert**\n\n"
            f"👤 **Name:** [{full_name}]({permanent_link})\n"
            f"📛 **Username:** @{username if username != 'No Username' else 'No Username'}\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"🔗 **Profile Link:** [Click Here]({permanent_link})\n"
            f"👥 **Total Users:** {total_users}",
            link_preview=False
        )

    # Inform User
    user_reporting[user_id] = {'status': 'idle'}
    await event.reply(
        f"<b>👋🏻 Welcome, <a href='{permanent_link}'>{full_name}</a>! 🎉</b>\n\n"
        "<i>We're excited to have you here! 🚀 With this bot, you can report any Instagram account effortlessly.</i>\n\n"
        "<blockquote>📌 <b>Steps to Get Started:</b>\n"
        "1️⃣ Join our channel to unlock all features.\n"
        "2️⃣ Use the /report command to start reporting your target.</blockquote>\n\n"
        "💡 <i>Need help? Reach out to our support team anytime!</i>",
        buttons=[
            [
                Button.url("📢 Update", "https://t.me/+WPKg3Ci2sMBkMDc1"),
                Button.url("🛠 Support", "https://t.me/offchats")
            ],
            [
                Button.url("👤 Admin", "https://t.me/CodeRehan"),
                Button.url("👨‍💻 Developer", "https://t.me/Seiao")
            ]
        ],
        parse_mode="html"
    )

# Report Command
@bot.on(events.NewMessage(pattern='/report'))
async def report_command(event):
    user_id = event.sender_id
    if not await is_user_in_channel(user_id):
        await event.reply(
            "👋🏻**Hey! You must join our channel to use this bot.**",
            buttons=[Button.url("Offchats", f"https://t.me/{CHANNEL_USERNAME}"),
Button.url("Python-Botz", "https://t.me/+WPKg3Ci2sMBkMDc1   ")]
        )
        return

    if user_reporting[user_id]['status'] != 'idle':
        await event.reply("⚠️ You already have a report in process. Finish that first.")
        return

    user_reporting[user_id]['status'] = 'awaiting_username'
    await event.reply(
        "⚠️ Note: Reporting an Instagram account can take a long time. Please be patient. Do not report accounts that are patched.",
        link_preview=False
    )

# Handle Username Submission
@bot.on(events.NewMessage)
async def handle_username(event):
    user_id = event.sender_id
    if user_reporting.get(user_id, {}).get('status') == 'awaiting_username':
        username = event.text.strip()
        if not username.startswith('@'):
            await event.reply("👤 Please send the username of your target (with @).")
            return

        instagram_link = f"[{username}](http://instagram.com/{username[1:]})"
        user_reporting[user_id] = {'status': 'reporting', 'username': username, 'count': 0, 'link': instagram_link}

        await event.reply(
            f"✅ Username `{username}` accepted.\nInstagram Link: {instagram_link}. Shall we start reporting?",
            buttons=[
                [Button.inline("Start Reporting", b'start_reporting')],
                [Button.inline("Cancel", b'cancel_reporting')]
            ]
        )

# Handle Inline Buttons
@bot.on(events.CallbackQuery)
async def callback(event):
    user_id = event.sender_id
    if event.data == b'start_reporting':
        if user_reporting[user_id]['status'] != 'reporting':
            await event.answer("❌ Invalid action.", alert=True)
            return
        await start_reporting(event)
    elif event.data == b'cancel_reporting':
        user_reporting[user_id]['status'] = 'idle'
        await event.edit("❌ Reporting process has been cancelled.")
    elif event.data == b'stop_reporting':
        user_reporting[user_id]['status'] = 'idle'
        username = user_reporting[user_id].get('username', 'Unknown')
        await event.edit(f"🛑 Reporting for {username} has been stopped. Total Reports: {user_reporting[user_id]['count']}.")

# Reporting Function
async def start_reporting(event):
    user_id = event.sender_id
    username = user_reporting[user_id]['username']

    message = await event.edit(
        f"🚀 Reporting {username}...",
        buttons=[[Button.inline("Stop Reporting", b'stop_reporting')]]
    )

    for i in range(1, 10001):
        if user_reporting[user_id]['status'] != 'reporting':
            await message.edit(f"‼️ Reporting {username} stopped. Total reports: {i}.")
            return

        user_reporting[user_id]['count'] = i
        await message.edit(
            f"✅ Reported {username} {i} times.",
            buttons=[[Button.inline("🛑 Stop Reporting", b'stop_reporting')]]
        )
        await asyncio.sleep(1)

    await message.edit(f"✅ Reporting for {username} completed (10,000 times).")

# Broadcast Command
@bot.on(events.NewMessage(pattern='/broadcast'))
async def broadcast(event):
    global broadcasting, waiting_for_broadcast_message
    if not event.sender_id == ADMIN_ID:
        return await event.reply("❌ Only admins can send broadcasts.")

    if broadcasting:
        await event.reply("🚨 A broadcast is already in progress!")
        return

    broadcasting = True
    waiting_for_broadcast_message = event
    await event.reply("📝 Please send the message you want to broadcast to all users:")

# Handle Broadcast Message
@bot.on(events.NewMessage)
async def handle_broadcast_message(event):
    global broadcasting, broadcast_message_content
    if broadcasting and event.sender_id == ADMIN_ID:
        broadcast_message_content = event.text
        broadcasting = False
        for user_id in active_users:
            try:
                await bot.send_message(user_id, broadcast_message_content)
            except Exception as e:
                print(f"Failed to send to {user_id}: {str(e)}")

        await event.reply("✅ Broadcast message sent to all users!")

# Run the Bot
print("🤖 Bot is running...")
bot.run_until_disconnected()
  
