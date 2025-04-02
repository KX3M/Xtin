import asyncio
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipant

# Bot Configuration
API_ID = '21259513'
API_HASH = '29e43fc190ebaef2ee94542cafb0614d'
BOT_TOKEN = 'YOUR_BOT_TOKEN'
CHANNEL_USERNAME = 'offchats'  # Replace with your channel username
ADMIN_ID = 6076683960  # Replace with your admin's Telegram ID

# Initialize bot
bot = TelegramClient('report_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Global Variables
user_reporting = {}
active_users = set()
broadcasting = False

# Helper Function: Check Channel Membership
async def is_user_in_channel(user_id):
    try:
        participant = await bot(GetParticipantRequest(CHANNEL_USERNAME, user_id))
        return isinstance(participant.participant, ChannelParticipant)
    except:
        return False

# Start Command: Force Join + Welcome Message
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id

    # Check if user is in the channel
    if not await is_user_in_channel(user_id):
        await event.reply(
            "👋🏻 **Hey! You must join our channel to use this bot.**",
            buttons=[Button.url("Join Channel", f"https://t.me/{CHANNEL_USERNAME}")]
        )
        return

    active_users.add(user_id)
    await event.reply(
        "👋 Welcome! Use /report to report an Instagram username.",
        buttons=[[Button.text("/report", resize=True)]]
    )

# Report Command
@bot.on(events.NewMessage(pattern='/report'))
async def report_command(event):
    user_id = event.sender_id
    if not await is_user_in_channel(user_id):
        await event.reply(
            "🚨 **You must join our channel to use this feature.**",
            buttons=[Button.url("Join Channel", f"https://t.me/{CHANNEL_USERNAME}")]
        )
        return

    user_reporting[user_id] = {'status': 'awaiting_username'}
    await event.reply("📢 **Send the Instagram username (with @) you want to report.**")

# Handle Username Submission
@bot.on(events.NewMessage)
async def handle_username(event):
    user_id = event.sender_id
    if user_reporting.get(user_id, {}).get('status') == 'awaiting_username':
        username = event.text.strip()
        if not username.startswith('@'):
            await event.reply("⚠️ **Please send a valid Instagram username (with @).**")
            return

        user_reporting[user_id] = {'status': 'reporting', 'username': username, 'count': 0}
        await event.reply(
            f"✅ Username `{username}` accepted.\n\n📢 **Shall we start reporting?**",
            buttons=[
                [Button.inline("🚀 Start Reporting", b'start_reporting')],
                [Button.inline("❌ Cancel", b'cancel_reporting')]
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
        await event.edit("🚫 Reporting process has been cancelled.")
    elif event.data == b'stop_reporting':
        user_reporting[user_id]['status'] = 'idle'
        await event.edit("🛑 Reporting stopped.")

# Reporting Function
async def start_reporting(event):
    user_id = event.sender_id
    username = user_reporting[user_id]['username']

    message = await event.edit(
        f"🚀 Reporting {username}...",
        buttons=[[Button.inline("🛑 Stop Reporting", b'stop_reporting')]]
    )

    for i in range(1, 10001):
        if user_reporting[user_id]['status'] != 'reporting':
            await message.edit(f"🛑 Reporting stopped. Total reports: {i}.")
            return

        user_reporting[user_id]['count'] = i
        await message.edit(f"✅ Reported {username} {i} times.")
        await asyncio.sleep(1)

    await message.edit(f"✅ Reporting for {username} completed (10,000 times).")

# Broadcast Command (Fixed)
@bot.on(events.NewMessage(pattern='/broadcast'))
async def broadcast(event):
    global broadcasting

    if event.sender_id != ADMIN_ID:
        return await event.reply("❌ **Only admins can use this command.**")

    await event.reply("📝 **Send the message you want to broadcast to all users.**")

    response = await bot.wait_for(events.NewMessage(from_users=ADMIN_ID))
    broadcast_message_content = response.text
    broadcasting = True
    success_count, failed_count = 0, 0

    await event.reply("🚀 **Broadcasting started...**")

    for user_id in active_users:
        try:
            await bot.send_message(user_id, broadcast_message_content)
            success_count += 1
        except:
            failed_count += 1

    broadcasting = False

    await bot.send_message(
        ADMIN_ID,
        f"✅ **Broadcast Completed!**\n\n📨 Sent: {success_count} users\n⚠️ Failed: {failed_count} users"
    )

# Run the Bot
print("🤖 Bot is running...")
bot.run_until_disconnected()
