from discord.ext import tasks
import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp # NEW
from collections import deque # NEW
import asyncio
import sqlite3
from datetime import datetime, timedelta, time
import random
import pytz
# from keep_alive import keep_alive
import googletrans
import matplotlib.pyplot as plt
import numpy as np
import io
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))
profanities = []

afk_users = {}

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID") or os.getenv("SPOTIPY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET") or os.getenv("SPOTIPY_CLIENT_SECRET")

sp = None
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    ))
else:
    print("Spotify credentials not found. Set SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET or SPOTIPY_CLIENT_ID / SPOTIPY_CLIENT_SECRET in .env to enable music playback.")


def create_tbl():
    conn = sqlite3.connect(f"{BASE_DIR}\\user_warns.db")
    cursor = conn.cursor()

    # Tracks the running warn count per user per guild
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS upg (
            uid   INTEGER NOT NULL,
            gid   INTEGER NOT NULL,
            WarnCnt INTEGER DEFAULT 0,
            PRIMARY KEY (uid, gid)
        )
    """)

    # Logs every individual warn with reason + timestamp
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warn_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            uid       INTEGER NOT NULL,
            gid       INTEGER NOT NULL,
            reason    TEXT DEFAULT 'No reason provided',
            warned_by INTEGER,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
create_tbl()


def inc_dec_warns(uid: int, gid: int, reason: str = "No reason provided", warned_by: int = None):
    conn = sqlite3.connect(f"{BASE_DIR}\\user_warns.db")
    cursor = conn.cursor()

    # Upsert the count
    cursor.execute("""
        INSERT INTO upg (uid, gid, WarnCnt) VALUES (?, ?, 1)
        ON CONFLICT(uid, gid) DO UPDATE SET WarnCnt = WarnCnt + 1
    """, (uid, gid))

    # Always insert a new log entry
    cursor.execute("""
        INSERT INTO warn_log (uid, gid, reason, warned_by)
        VALUES (?, ?, ?, ?)
    """, (uid, gid, reason, warned_by))

    cursor.execute("SELECT WarnCnt FROM upg WHERE uid = ? AND gid = ?", (uid, gid))
    count = cursor.fetchone()[0]

    conn.commit()
    conn.close()
    return count


TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default() 
intents.message_content = True  


bot = commands.Bot(command_prefix=".", intents=intents)


gid = 1466069152338018328
# last_creator_greeting = {}  # Track last greeting time for creator
  # Track AFK users with their reasons

#-------------------------------------------------------------------------------


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global command(s).")
    except Exception as e:
        print(f"Error syncing: {e}")
        
    print(f"{bot.user} is online!")
    await bot.change_presence(activity = discord.Game(name=".help | Music & Moderation"))
    chanid = [1488807844701536358,1496113868487786636]
    for i in chanid:
        chan = bot.get_channel(i)
        if chan:
            
            embed3 = discord.Embed(title="Status", description=f"🟢 **Online**", color=discord.Color.orange())
            await chan.send(embed=embed3)
    with open(os.path.join(BASE_DIR, "changelogs.txt"), "r", encoding="UTF-8") as fp:
        x = fp.read()
    l = [1488627485170991244,1488630540318933002]
    for j in l:
        clogs = bot.get_channel(j)
        if clogs is None:
            try:
                clogs = await bot.fetch_channel(j)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                continue
        if clogs:
            embed5 = discord.Embed(title="Status", description=f"{x}", color=discord.Color.orange())
            await clogs.send(embed=embed5)
        

@bot.event
async def on_message(msg):
    if msg.author.id != bot.user.id:
        for i in profanities:
            if i.lower() in msg.content.lower():
                num_warnings = inc_dec_warns(msg.author.id,msg.guild.id)

                if num_warnings >= 5:
                    duration = timedelta(minutes=5)
                    await msg.author.timeout(duration,reason="Excessive profanity.")
                    await msg.channel.send(f"{msg.author.mention} has been timed out for excessive profanity.")

                else:
                    await msg.channel.send(
                        f"**Warning {num_warnings}/5** {msg.author.mention}❗. You will be timed out after 5 Warnings."
                    )

                    await msg.delete()
                break
    
    if msg.author.id in afk_users:

        try:
            
            await msg.author.edit(nick=msg.author.display_name.replace("[AFK] ", ""))
        except discord.Forbidden:
            pass  # Can't change nickname, but remove AFK status anyway
        await msg.channel.send(f"{msg.author.mention} Welcome back!")
        del afk_users[msg.author.id]
        print(f"{msg.author} is no longer AFK.")
    await bot.process_commands(msg)

    if msg.author.id != bot.user.id:
        if (msg.content.startswith("<@") and msg.content.endswith(">")):
            # Extract user ID from mention
            user_id = int(msg.content[2:-1])
            if user_id in afk_users:
                reason = afk_users[user_id]
                await msg.channel.send(f"{msg.content} is currently AFK. Reason: {reason}")

#-------------------------------------------------------------------------------
def changelogs():
    try:

        fp = open(f"{BASE_DIR}\\changelogs.txt","r", encoding="utf-8")
        x = fp.read()
    except FileNotFoundError:
        x = "Changelogs not found."
    return x
        

@bot.hybrid_command(name="changelog", description="Shows the latest changelogs of the bot")
@app_commands.describe(channel_id="Channel ID to post changelogs")
async def changelog(ctx: commands.Context, channel_id: int = None):
    logs = changelogs()
    if len(logs) > 4096:
        logs = logs[:4093] + "..."
    embed = discord.Embed(title="TCore Changelogs", description=logs, color=discord.Color.red())

    if channel_id is None:
        await ctx.send(embed=embed)
        return

    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except discord.NotFound:
            await ctx.send("Channel not found. Please check the channel ID.")
            return
        except discord.Forbidden:
            await ctx.send("I can't access that channel. Make sure the bot has permission.")
            return
        except discord.HTTPException as e:
            await ctx.send(f"Failed to fetch channel: {e}")
            return

    try:
        await channel.send(embed=embed)
        await ctx.send(f"Changelog posted to <#{channel_id}>")
    except discord.Forbidden:
        await ctx.send("I don't have permission to send messages in that channel.")
    except discord.HTTPException as e:
        await ctx.send(f"Failed to send message: {e}")


#-------------------------------------------------------------------------------
@bot.hybrid_command(name = "poll", description = "Creates a poll with given options")
@app_commands.describe(
    question = "The poll question",
    options = "The poll options separated by commas (max 5)"
)
async def poll(ctx: commands.Context, question: str, options: str):
    option_list = [opt.strip() for opt in options.split(",") if opt.strip()]
    
    if len(option_list) < 2:
        await ctx.send("Please provide at least 2 options for the poll.")
        return
    if len(option_list) > 5:
        await ctx.send("Please provide no more than 5 options for the poll.")
        return

    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    description = "\n".join(f"{emojis[i]} {option}" for i, option in enumerate(option_list))
    
    embed = discord.Embed(title=question, description=description, color=discord.Color.red())
    poll_message = await ctx.send(embed=embed)

    for i in range(len(option_list)):
        await poll_message.add_reaction(emojis[i])

#------------------------------------------------------------------------

@bot.hybrid_command(name="translate", description="translates a given message")

async def trans(ctx: commands.Context):
    if ctx.message.reference:  #checks for message reply or not
        rep_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        text = rep_msg.content
        translator = googletrans.Translator()
        try:
            res = translator.translate(text)
            await ctx.send(f"**__Translation- __**{res.text}")
        except Exception as e:
            await ctx.send(f"Translation failed: {str(e)}")

#------------------------------------------------------------------------
snipe_message_cache = {}

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    # Store the deleted message info by channel ID
    snipe_message_cache[message.channel.id] = {
        'author': message.author,
        'content': message.content,
        'attachments': message.attachments if message.attachments else None,
        'time': message.created_at
    }
    print(snipe_message_cache)


@bot.hybrid_command(name="snipe", description="Retrieve the last deleted message in the channel")
async def snipe(ctx: commands.Context):
    # Check if there's a cached deleted message for this channel
    if ctx.channel.id not in snipe_message_cache:
        await ctx.send("No deleted messages to snipe!")
        return
    
    data = snipe_message_cache[ctx.channel.id]

    # Check if the message had text content
    if data['content']:
        await ctx.send(f"Last deleted message by {data['author'].mention}: \"{data['content']}\"")
    elif data['attachments']:
        attachment_urls = ', '.join(attachment.url for attachment in data['attachments'])
        await ctx.send(f"Last deleted message by {data['author'].mention} had attachments: {attachment_urls}")

#-------------------------------------------------------------------------------

@bot.hybrid_command(name="afk", description="Sets your status to AFK")
@app_commands.describe(reason="The reason for going AFK")
async def afk(ctx: commands.Context, reason: str = "No reason provided"):
    try:
        await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}")
        afk_users[ctx.author.id] = reason
        await ctx.send(f"{ctx.author.mention} is now AFK. Reason: {reason}")
        print(f"{ctx.author} is now AFK. Reason: {reason}")
    except discord.Forbidden:
        afk_users[ctx.author.id] = reason
        await ctx.send(f"{ctx.author.mention}, I can't change your nickname, but you're marked as AFK. Reason: {reason}")
        await ctx.send(f"**__Note: My role must be higher than yours to change your nickname.__**")
        print(f"{ctx.author} is now AFK. Reason: {reason}")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

#----------------------------------------------------------------------
@bot.hybrid_command(name="mute", description="Mutes a user for given time duration")
@commands.has_permissions(moderate_members=True)
@commands.bot_has_permissions(moderate_members=True)
@app_commands.describe(
    member = "The user you want to mute",
    duration = "The duration of the mute in minutes")

async def mute(ctx: commands.Context,member: discord.Member,duration: int):
    duration = timedelta(minutes=duration)
    try:
        await member.edit(nick=f"[MUTED] {member.display_name}")
    except discord.Forbidden:
        await ctx.send(f"**__Note: My role must be higher than {member.display_name}'s role to change their nickname.__**")
        print("Cannot change nickname for muted user.")
    if duration <= timedelta(0):
        await ctx.send("Please specify a valid duration for the mute.")
        return
    else:
        await member.timeout(duration,reason=f"Muted by {ctx.author.mention} for {duration}")
        await ctx.send(f"{member.mention} has been muted for {duration}.")
        print(f"{member} has been muted for {duration} by {ctx.author}.")

#-----------------------------------------------------------------------

@bot.hybrid_command(name="unmute",description = "Unmutes a user")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.describe(
    member = "The user you want to unmute")

async def unmute(ctx: commands.Context,member: discord.Member):
    try:
        await member.edit(nick=member.display_name.replace("[MUTED] ", ""))
    except discord.Forbidden:
        print("Cannot change nickname for unmuted user.")
    await member.timeout(None,reason=f"Unmuted by {ctx.author.mention}")
    await ctx.send(f"{member.mention} has been unmuted.")

#-----------------------------------------------------------------------

@bot.hybrid_command(name="ping",description = "Pings the bot to check if it's online")
async def ping(ctx: commands.Context):
    await ctx.send("Pong!")

#_________________________________________________________________________

@bot.hybrid_command(name="purge",description = "Purges a given number of messages from the channel")
@commands.has_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True)
@app_commands.describe(
    amount = "The number of messages to purge")

async def purge(ctx: commands.Context,amount: int):
    if not ctx.channel:
        await ctx.send("This command cannot be used in this context.")
        return
    if amount < 1:
        await ctx.send("Please specify a valid number of messages to purge.")
        return
    if amount > 100:
        await ctx.send("Please specify a number of messages less than 100.")
        return
    if ctx.interaction:
        await ctx.interaction.response.defer(ephemeral=True)
    try:
        deleted = await ctx.channel.purge(limit=amount)
        if ctx.interaction:
            await ctx.interaction.followup.send(f"**Deleted {len(deleted)} messages.**",ephemeral=True)
        else:
            await ctx.send(f"**Deleted {len(deleted)} messages.**")
    except discord.Forbidden:
        await ctx.send("I don't have permission to manage messages in this channel.")


#----------------------------------------------------------------------------------
#DIsabled the plot commands due to Async issues.

# @bot.hybrid_command(name = "plot", description="Plots a math function")
# @app_commands.describe(
#     func = "Function of x to plot",
#     xmin = "minimum value of x",
#     xmax = "maximum value of x",
# )

# async def plot(ctx: commands.Context, func: str,xmin:float=-10.0,xmax: float=10.0):
#     await ctx.defer()
#     try:
#         x = np.linspace(xmin,xmax,500)
#         y = np.clip(eval(func,{"__builtins__":{}},{**vars(np),"x":x}),-1000,1000)
#         plt.figure()
#         plt.plot(x,y)
#         plt.title(f"f(x) = {func}")
#         plt.grid(True)

#         b = io.BytesIO()
#         plt.savefig(b,format="png")
#         b.seek(0)
#         plt.close()
#         await ctx.send(file=discord.File(b,"plot.png"))
#     except Exception:
#         await ctx.send("Invalid function or error in plotting.")

#-----------------------------------------------------------------------
@bot.hybrid_command(name="info",description = "Gives info about the bot")
async def info(ctx: commands.Context):
    await ctx.send("TCore, a multifunctional Discord bot created to assist with moderation. Developed with discord.py, I aim to enhance your server experience!\n\nCreated by: Subhojit_.nvm")
#-----------------------------------------------------------------------
@bot.hybrid_command(name="warn",description = "warns a user")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.describe(
    member = "The user you want to warn",
    reason = "The reason for the warning")

async def warn(ctx: commands.Context,member: discord.Member,reason: str = "No reason provided"):
    await ctx.defer()
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    numwarns = inc_dec_warns(member.id,ctx.guild.id)
    
    if numwarns >= 5:
        duration = timedelta(minutes=5)
        await member.timeout(duration,reason=f"{numwarns}/5 Reached warnings: {reason}")
        await ctx.send(f"{member.mention} has been timed out. {numwarns}/5 Warnings. Reason: {reason}")
    else:
        await ctx.send(f"⚠️{member.mention} has been warned for reason: {reason}. [{numwarns} Warnings.]")

#----------------------------------------------------------------------------------------------------------------

@bot.hybrid_command(name="clearwarn",description="clears all warnings from given user")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.describe(
    member = "The user you want to clear warnings from")

async def clearwarn(ctx: commands.Context, member: discord.Member):
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    conn = sqlite3.connect(f"{BASE_DIR}\\user_warns.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM upg WHERE uid = ? AND gid = ?", (member.id, ctx.guild.id))
    cursor.execute("DELETE FROM warn_log WHERE uid = ? AND gid = ?", (member.id, ctx.guild.id))

    conn.commit()
    conn.close()
    await ctx.send(f"All warnings cleared from {member.mention}.")
#----------------------------------------------------------------------------------------------------------------
@bot.hybrid_command(name="cases", description="View warning history of a user")
@app_commands.checks.has_permissions(moderate_members=True)
async def cases(ctx: commands.Context, member: discord.Member):
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    conn = sqlite3.connect(f"{BASE_DIR}\\user_warns.db")
    cursor = conn.cursor()

    cursor.execute("SELECT WarnCnt FROM upg WHERE uid = ? AND gid = ?", (member.id, ctx.guild.id))
    row = cursor.fetchone()
    count = row[0] if row else 0

    cursor.execute("""
        SELECT reason, warned_by, timestamp FROM warn_log
        WHERE uid = ? AND gid = ?
        ORDER BY timestamp DESC LIMIT 10
    """, (member.id, ctx.guild.id))
    logs = cursor.fetchall()
    conn.close()


    embed = discord.Embed(title=f"⚠️ Warnings — {member.display_name}", color=discord.Color.orange())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Total Warns", value=f"{count}/5", inline=False)

    if logs:
        history = "\n".join(
            f"`{t}` — {r} (by <@{b}>)" for r, b, t in logs
        )
        embed.add_field(name="History (last 10)", value=history, inline=False)
    else:
        embed.add_field(name="History", value="No warn logs found.", inline=False)

    await ctx.send(embed=embed)

#--------------------------------------------------------------------------------
@bot.hybrid_command(name= "avatar", description="Shows the avatar of the user")
@app_commands.describe(
    member = "The user whose avatar you want to see (optional)"
)

async def avatar(ctx: commands.Context, member: discord.Member = None):
    x = member or ctx.author
    embed  = discord.Embed(title = f"{x.display_name}'s Avatar", color = discord.Color.yellow())
    embed.set_image(url=x.display_avatar.url)
    await ctx.send(embed=embed)

#----------------------------------------------------------------------------------------------------------------

@bot.hybrid_command(name = "kick", description = "Kicks a user from the server")
@app_commands.checks.has_permissions(kick_members=True)
@app_commands.describe(
     member = "the user you want to kick",
     reason = "the reason for kicking"
)
async def kick(ctx: commands.Context, member: discord.Member, reason: str= "No reason provided"):
     await member.kick(reason = reason)
     await ctx.send(f"{member.mention} has been kicked from the server by Moderator {ctx.author.mention} for reason: {reason}")
#----------------------------------------------------------------------------------------------------------
@bot.hybrid_command(name="ban",description="Bans a user from the server")
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.describe(
     member = "the user you want to ban",
     reason = "the reason for banning"
)

async def ban(ctx: commands.Context, member: discord.Member, reason: str = "No reason provided"):
     await member.ban(reason=reason)
     await ctx.send(f"{member.mention} has been banned from the server by Moderator {ctx.author.mention} for reason: {reason}")

#----------------------------------------------------------------------------------------------------------

@bot.hybrid_command(name = "unban", description="Unbans a user from the server")
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.describe(
     user = "the discord ID of the user to be unbanned"
)

async def unban(ctx: commands.Context, user: str):
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    idint = int(user)

    await ctx.guild.unban(discord.Object(id=idint))
    await ctx.send(f"User {idint} successfully unbanned by Moderator {ctx.author.mention}.")
     

#--------------------------------------------------------------------------------------------------------------------------

@bot.hybrid_command(name="greet",description = "Sends a heartful Greeting!")
async def greet(ctx: commands.Context):
    username = ctx.author.mention
    await ctx.send(f"Hey there!, {username}")

#-------------------------------------------------------------------------------------------------------------------------
@bot.hybrid_command(name = "remind",description="Remind you in the given time interval in your DM")
@app_commands.describe(
    time = "The time after which you want to be reminded (in minutes)",
    reminder = "The reminder message you want to receive"

)
async def remind(ctx: commands.Context, time: int, reminder: str):
    await ctx.send(f"TCore will remind you in {time} minutes!")
    await asyncio.sleep(time * 60)
    try:
        await ctx.author.send(f"**Reminder** : {reminder}")
    except discord.Forbidden:
        await ctx.send(f"{ctx.author.mention}, I can't send you a DM. Please check your privacy settings.")

#--------------------------------------------------------------------------------------------------------------------------
@bot.hybrid_command(name = "shut" , description="Shuts down bot")
@commands.is_owner()

async def shutdown(ctx):
    embed4 = discord.Embed(title="Status", description=f"🔴 **Shutting Down**", color=discord.Color.orange())
    await ctx.send(embed = embed4)
    await bot.close()

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN is not set. Add it to your environment or .env file.")
    bot.run(TOKEN)
