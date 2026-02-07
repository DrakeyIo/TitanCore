from discord.ext import tasks
import os
from signal import signal
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
from keep_alive import keep_alive
import googletrans
keep_alive()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


profanities = ["nigger"]

afk_users = {}


def create_tbl():
    conn = sqlite3.connect(f"{BASE_DIR}\\user_warns.db")
    cursor = conn.cursor()


    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS "upg"(
                   "uid" INT,
                   "WarnCnt" INT,
                   "gid" INT,
                   PRIMARY KEY("uid","gid"))""")
    
    conn.commit()
    conn.close()
    
create_tbl()


def inc_dec_warns(uid: int, gid: int):
    conn = sqlite3.connect(f"{BASE_DIR}\\user_warns.db")
    cursor = conn.cursor()

    cursor.execute("""
                   SELECT WarnCnt FROM upg
                   WHERE (uid = ?) AND (gid = ?);""",(uid,gid))                

    result = cursor.fetchone()

    if result == None:
        cursor.execute("""
                       INSERT INTO upg(uid,WarnCnt,gid)
                       VALUES(?,1,?);""",
                       (uid,gid))

        conn.commit()
        conn.close()
        
        return 1

    cursor.execute("""
                   UPDATE upg
                   SET WarnCnt = ?
                   WHERE (uid = ?) AND (gid = ?);""",
                   (result[0] + 1,uid,gid))
    conn.commit()
    conn.close()

    return result[0] + 1


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default() 
intents.message_content = True  


bot = commands.Bot(command_prefix=".", intents=intents)


gid = 1466069152338018328
last_creator_greeting = {}  # Track last greeting time for creator
  # Track AFK users with their reasons

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global command(s).")
    except Exception as e:
        print(f"Error syncing: {e}")
        
    print(f"{bot.user} is online!")
    await bot.change_presence(activity = discord.Game(name=".help | Music & Moderation"))
    chanid = [1357797238243328174]
    chan = bot.get_channel(chanid[0])
    if chan:
        await chan.send("**TCore is now online!, Music Features are currently disabled for maintenance.**")
    else:
        print("Channel not found.")
    if not morning_wish.is_running():
        morning_wish.start()


@tasks.loop(time=time(9, 0, 0, tzinfo=pytz.timezone("Asia/Kolkata")))
async def morning_wish():
    channel = await bot.fetch_channel(1357797238243328174)  
    await channel.send(f"**<@1358003603343933490> Good morning Fellas! freshen up and make the day count! ☀️**")

rom = ["Sunday dilam Shilake","Monday dilam Mona ke","Tuesday dilam Tina ke","Wednesday Oindrila ke","Thurday dilam Riya ke","Friday dilam Diya ke","Saturday ta Priya ke","Dil to deyni karoke"]

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
    

    if msg.author.id == 797379227204321381:

        cid = 797379227204321381
        time = datetime.now()

        if cid not in last_creator_greeting:
             
             last_creator_greeting[cid] = time
             await msg.channel.send(f"{msg.author.mention} Hey Creator!, hows it going?")
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
    if msg.author.id != bot.user.id:
        if msg.content.startswith("psps"):
            await msg.channel.send("Paws Paws! 🥺😼")

    if msg.author.id != bot.user.id:
        if "romeo" in msg.content.lower():
            for i in rom:
                await msg.channel.send(i)


@bot.hybrid_command(name="translate", description="translates a given message")

async def afk(ctx: commands.Context):
    if ctx.message.reference:  #checks for message reply or not
        rep_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        text = rep_msg.content
        trans = googletrans.Translator()
        res = await trans.translate(text)
        await ctx.send(f"**__Translation- __**{res.text}")






@bot.hybrid_command(name="chod", description="chod")
async def chod(ctx:commands.Context):
    await ctx.send(f"https://media.discordapp.net/attachments/1435324014737358982/1469007738246791289/magical_wallet.mp4?ex=69861791&is=6984c611&hm=70d169366228c17fa20b8b35639ffa35c689cca0cd3914fdf81c7752e435df0f&")

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

@bot.hybrid_command(name="unsee", description="Pretend you didn't see the last message")
async def unsee(ctx:commands.Context):
    await ctx.send(f"{ctx.author.mention} pretended they didn't see that absolute crap of a message.")
@bot.hybrid_command(name="unfriend", description="Unfriend")
async def unfriend(ctx:commands.Context):
    await ctx.send(f"https://cdn.discordapp.com/attachments/1435324014737358982/1468941622938173472/1650700117674_.mp4?ex=6985d9fe&is=6984887e&hm=06d29b91a9153de196e31eba4c870878370a80aae5fd73ae917f95b74bda1dde&")
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
@bot.hybrid_command(name="mute",description = "Mutes a user for given time duration")
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
        pass  # Can't change nickname, but proceed with muting
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
        pass  # Can't change nickname, but proceed with unmuting
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


#-----------------------------------------------------------------------

@bot.hybrid_command(name="info",description = "Gives info about the bot")
async def info(ctx: commands.Context):
    await ctx.send("I am TCore, a multifunctional Discord bot created to assist with moderation and provide entertainment through music playback. Developed with Python and discord.py, I aim to enhance your server experience!"
    "n\nCreated by: Subhojit_.nvm")

@bot.hybrid_command(name="warn",description = "warns a user")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.describe(
    member = "The user you want to warn",
    reason = "The reason for the warning")

async def warn(ctx: commands.Context,member: discord.Member,reason: str = "No reason provided"):
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

async def clearwarn(ctx: commands.Context,member: discord.Member):
     conn = sqlite3.connect(f"{BASE_DIR}\\user_warns.db")
     cursor = conn.cursor()

     cursor.execute("""
                    UPDATE upg
                    set WarnCnt = 0
                    WHERE (uid = ?) AND (gid = ?);""",
                    (member.id,ctx.guild.id))
     conn.commit()
     conn.close()

     await ctx.send(f"All warnings cleared from {member.mention}.")


@bot.hybrid_command(name="cases",description="views the number of warnings a user has")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.describe(
    member = "The users warnings you want to view")

async def cases(ctx: commands.Context,member: discord.Member):
        conn = sqlite3.connect(f"{BASE_DIR}\\user_warns.db")
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT WarnCnt FROM upg
                       WHERE (uid = ?) AND (gid = ?);""",
                    (member.id,ctx.guild.id))
        
        result = cursor.fetchone()
        conn.close()
        if (result[0] == 1):
            await ctx.send(f"{member.mention} has {result[0]} Warning.")
        else:
              await ctx.send(f"{member.mention} has {result[0]} Warnings.")

#---------------------------------------------------------------


@bot.hybrid_command(name = "kick", description = "Kicks a user from the server")
@app_commands.checks.has_permissions(kick_members=True)
@app_commands.describe(
     member = "the user you want to kick",
     reason = "the reason for kicking"
)
async def kick(ctx: commands.Context, member: discord.Member, reason: str= "No reason provided"):
     await member.kick(reason = reason)
     await ctx.send(f"{member.mention} has been kicked from the server by Moderator {ctx.user.mention} for reason: {reason}")

@bot.hybrid_command(name="ban",description="Bans a user from the server")
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.describe(
     member = "the user you want to ban",
     reason = "the reason for banning"
)

async def ban(ctx: commands.Context, member: discord.Member, reason: str = "No reason provided"):
     await member.ban(reason=reason)
     await ctx.send(f"{member.mention} has been banned from the server by Moderator {ctx.author.mention} for reason: {reason}")


@bot.hybrid_command(name = "unban", description="Unbans a user from the server")
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.describe(
     user = "the discord ID of the user to be unbanned"
)

async def unban(ctx: commands.Context, user: str):
     idint = int(user)

     await ctx.guild.unban(discord.Object(id=idint))
     await ctx.send(f"User {idint} successfully unbanned by Moderator {ctx.user.mention}.")
     

#--------------------------------------------------------------------------------------------------------------------------




@bot.hybrid_command(name="greet",description = "Sends a heartful Greeting!")
async def greet(ctx: commands.Context):
    username = ctx.user.mention
    await ctx.send(f"Hey there!, {username}")

#-------------------------------------------------------------------------------------------------------------------------
Current_song = {}      
GID = 1466069152338018328

# Create the structure for queueing songs - Dictionary of queues
SONG_QUEUES = {}

async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)


@bot.tree.command(name="skip", description="Skips the current playing song")
async def skip(ctx: commands.Context):
    if ctx.guild.voice_client and (ctx.guild.voice_client.is_playing() or ctx.guild.voice_client.is_paused()):
        ctx.guild.voice_client.stop()
        await ctx.send("Skipped the current song.")
    else:
        await ctx.send("Not playing anything to skip.")


@bot.tree.command(name="pause", description="Pause the currently playing song")
async def pause(ctx: commands.Context):
    voice_client = ctx.guild.voice_client

    # Check if the bot is in a voice channel
    if voice_client is None:
        return await ctx.send("I'm not in a voice channel.")

    # Check if something is actually playing
    if not voice_client.is_playing():
        return await ctx.send("Nothing is currently playing.")
    
    # Pause the track
    voice_client.pause()
    await ctx.send("Playback paused!")


@bot.tree.command(name="resume", description="Resume the currently paused song")
async def resume(ctx: commands.Context):
    voice_client = ctx.guild.voice_client   
    # Check if the bot is in a voice channel
    if voice_client is None:
        return await ctx.send("I'm not in a voice channel.")

    # Check if it's actually paused
    if not voice_client.is_paused():
        return await ctx.send("I’m not paused right now.")
    
    # Resume playback
    voice_client.resume()
    await ctx.send("Playback resumed!")

@bot.tree.command(name="stop", description="Stop playback and clear the queue.")
async def stop(interaction: discord.Interaction):
    ctx = interaction
    voice_client = ctx.guild.voice_client

    # Check if the bot is in a voice channel
    if not voice_client or not voice_client.is_connected():
        return await ctx.send("I'm not connected to any voice channel.")

    # Clear the guild's queue
    guild_id_str = str(ctx.guild.id)
    if guild_id_str in SONG_QUEUES:
        SONG_QUEUES[guild_id_str].clear()

    # If something is playing or paused, stop it
    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    # (Optional) Disconnect from the channel
    await voice_client.disconnect()

    await ctx.send("Stopped playback and disconnected!")


@bot.tree.command(name="play", description="Play a song or add it to the queue.")
@app_commands.describe(song_query="Search query")
async def play(interaction: discord.Interaction, song_query: str):
    await interaction.response.send_message("Music playback is currently disabled.", ephemeral=True)
#     await interaction.response.defer()

#     ctx = interaction
#     voice_channel = ctx.author.voice.channel

#     if voice_channel is None:
#         await ctx.followup.send("You must be in a voice channel.")
#         return

#     voice_client = ctx.guild.voice_client
#     if voice_client is None:
#         voice_client = await voice_channel.connect()
#     elif voice_channel != voice_client.channel:
#         await voice_client.move_to(voice_channel)

#     ydl_options = {
#         "format": "bestaudio[abr<=96]/bestaudio",
#         "noplaylist": True,
#         "youtube_include_dash_manifest": False,
#         "youtube_include_hls_manifest": False,
#     }

#     query = "ytsearch1: " + song_query
#     results = await search_ytdlp_async(query, ydl_options)
#     tracks = results.get("entries", [])

#     if tracks is None:
#         await ctx.followup.send("No results found.")
#         return

#     first_track = tracks[0]
#     audio_url = first_track["url"]
#     title = first_track.get("title", "Untitled")

#     guild_id = str(ctx.guild.id)
#     if SONG_QUEUES.get(guild_id) is None:
#         SONG_QUEUES[guild_id] = deque()

#     SONG_QUEUES[guild_id].append((audio_url, title))

#     if voice_client.is_playing() or voice_client.is_paused():
#         await ctx.followup.send(f"Added to queue: **{title}**")
#     else:
#         await ctx.followup.send(f"Now playing: **{title}**")
#         await play_next_song(voice_client, guild_id, ctx.channel)

# async def play_next_song(voice_client, guild_id, channel):
#     if SONG_QUEUES[guild_id]:
#         audio_url, title = SONG_QUEUES[guild_id].popleft()

#         ffmpeg_options = {
#             "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
#             "options": "-vn -c:a libopus -b:a 96k",
#             # Remove executable if FFmpeg is in PATH
#         }

#         source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options, executable="bin\\ffmpeg\\ffmpeg.exe")

#         def after_play(error):
#             if error:
#                 print(f"Error playing {title}: {error}")
#             asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)

#         voice_client.play(source, after=after_play)
#         asyncio.create_task(channel.send(f"Now playing: **{title}**"))
#     else:
#         await voice_client.disconnect()
#         SONG_QUEUES[guild_id] = deque()


@bot.tree.command(name="now", description="Shows the currently playing song")
async def now(interaction: discord.Interaction):
    await interaction.response.send_message("Now playing feature is currently disabled.", ephemeral=True)
    # ctx = interaction
    # voice_client = ctx.guild.voice_client
    # guild_id = str(ctx.guild.id)
    
    # if voice_client is None or not voice_client.is_connected():
    #     await ctx.response.send_message(f"The bot is not in a voice channel.")
    #     return
    
    # if not (voice_client.is_playing() or voice_client.is_paused()):
    #     await ctx.response.send_message(f"No song is currently playing.")
    #     return
    
    # if guild_id in Current_song:
    #     current_title = Current_song[guild_id]
    #     status = "⏸️ Paused" if voice_client.is_paused() else "▶️ Playing"
    #     await ctx.response.send_message(f"{status}: **{current_title}**")
    # else:
    #     await ctx.response.send_message(f"No song information available.")


# @bot.tree.command(name="meme", description= "Sends a random meme from meme folder")
# async def meme(interaction: discord.Interaction):
#     ctx = interaction
#     meme_folder = os.path.join(BASE_DIR, "memes")
#     meme_files = [f for f in os.listdir(meme_folder) if os.path.isfile(os.path.join(meme_folder, f))]
    
#     random_meme = os.path.join(meme_folder, random.choice(meme_files))
#     await ctx.response.send_message(file=discord.File(random_meme))


bot.run(TOKEN)











