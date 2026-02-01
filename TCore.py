import os
import random
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import sqlite3
from datetime import timedelta, datetime
import yt_dlp
import asyncio
from collections import deque



BASE_DIR = os.path.dirname(os.path.abspath(__file__))


profanities = ["nigger"]




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

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global command(s).")
    except Exception as e:
        print(f"Error syncing: {e}")
        
    print(f"{bot.user} is online!")




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
    await bot.process_commands(msg)

    if msg.author.id == 797379227204321381:
        cid = 797379227204321381
        time = datetime.now()
        if cid not in last_creator_greeting:
             last_creator_greeting[cid] = time
             await msg.channel.send(f"{msg.author.mention} Hey Creator!, hows it going?")
        elif time - last_creator_greeting[cid] >= timedelta(minutes=30):
             last_creator_greeting[cid] = time
             await msg.channel.send(f"{msg.author.mention} Hey Creator!, hows it going?")

#----------------------------------------------------------------------
@bot.tree.command(name="mute",description = "Mutes a user for given time duration")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.describe(
    member = "The user you want to mute",
    duration = "The duration of the mute in minutes")

async def mute(interaction: discord.Interaction,member: discord.Member,duration: int):
    duration = timedelta(minutes=duration)
    await member.timeout(duration,reason=f"Muted by {interaction.user.mention} for {duration}")
    await interaction.response.send_message(f"{member.mention} has been muted for {duration}.")

#-----------------------------------------------------------------------

@bot.tree.command(name="unmute",description = "Unmutes a user")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.describe(
    member = "The user you want to unmute")

async def unmute(interaction: discord.Interaction,member: discord.Member):
    await member.timeout(None,reason=f"Unmuted by {interaction.user.mention}")
    await interaction.response.send_message(f"{member.mention} has been unmuted.")

#-----------------------------------------------------------------------

@bot.tree.command(name="ping",description = "Pings the bot to check if it's online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


#-----------------------------------------------------------------------

@bot.tree.command(name="info",description = "Gives info about the bot")
async def info(interaction: discord.Interaction):
    await interaction.response.send_message("I am TCore, a multifunctional Discord bot created to assist with moderation and provide entertainment through music playback. Developed with Python and discord.py, I aim to enhance your server experience!"
    "n\nCreated by: Subhojit_.nvm")

@bot.tree.command(name="warn",description = "warns a user")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.describe(
    member = "The user you want to warn",
    reason = "The reason for the warning")

async def warn(interaction: discord.Interaction,member: discord.Member,reason: str = "No reason provided"):
    numwarns = inc_dec_warns(member.id,interaction.guild.id)
    
    if numwarns >= 5:
                    duration = timedelta(minutes=5)
                    await member.timeout(duration,reason=f"{numwarns}/5 Reached warnings: {reason}")
                    await interaction.response.send_message(f"{member.mention} has been timed out. {numwarns}/5 Warnings. Reason: {reason}")

    else:
         await interaction.response.send_message(f"⚠️{member.mention} has been warned for reason: {reason}. [{numwarns} Warnings.]")


#----------------------------------------------------------------------------------------------------------------


@bot.tree.command(name="clearwarn",description="clears all warnings from given user")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.describe(
    member = "The user you want to clear warnings from")

async def clearwarn(interaction: discord.Interaction,member: discord.Member):
     conn = sqlite3.connect(f"{BASE_DIR}\\user_warns.db")
     cursor = conn.cursor()

     cursor.execute("""
                    UPDATE upg
                    set WarnCnt = 0
                    WHERE (uid = ?) AND (gid = ?);""",
                    (member.id,interaction.guild.id))
     conn.commit()
     conn.close()

     await interaction.response.send_message(f"All warnings cleared from {member.mention}.")


@bot.tree.command(name="cases",description="views the number of warnings a user has")
@app_commands.describe(
    member = "The users warnings you want to view")

async def cases(interaction: discord.Interaction,member: discord.Member):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("Unauthorized.")
            return
        
        try:
            conn = sqlite3.connect(f"{BASE_DIR}\\user_warns.db")
            cursor = conn.cursor()

            cursor.execute("""
                           SELECT WarnCnt FROM upg
                           WHERE (uid = ?) AND (gid = ?);""",
                        (member.id,interaction.guild.id))
            
            result = cursor.fetchone()
            conn.close()
            
            if result is None:
                await interaction.response.send_message(f"{member.mention} has 0 Warnings.")
            elif result[0] == 1:
                await interaction.response.send_message(f"{member.mention} has {result[0]} Warning.")
            else:
                  await interaction.response.send_message(f"{member.mention} has {result[0]} Warnings.")
        except Exception as e:
            print(f"Error: {e} by {interaction.user.id}")
#---------------------------------------------------------------


@bot.tree.command(name = "kick", description = "Kicks a user from the server")
@app_commands.checks.has_permissions(kick_members=True)
@app_commands.describe(
     member = "the user you want to kick",
     reason = "the reason for kicking"
)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str= "No reason provided"):
     await member.kick(reason = reason)
     await interaction.response.send_message(f"{member.mention} has been kicked from the server by Moderator {interaction.user.mention} for reason: {reason}")


@bot.tree.command(name="ban",description="Bans a user from the server")
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.describe(
     member = "the user you want to ban",
     reason = "the reason for banning"
)

async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
     await member.ban(reason=reason)
     await interaction.response.send_message(f"{member.mention} has been banned from the server by Moderator {interaction.user.mention} for reason: {reason}")


@bot.tree.command(name = "unban", description="Unbans a user from the server")
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.describe(
     user = "the discord ID of the user to be unbanned"
)

async def unban(interaction: discord.Interaction, user: str):
     idint = int(user)

     await interaction.guild.unban(discord.Object(id=idint))
     await interaction.response.send_message(f"User {idint} successfully unbanned by Moderator {interaction.user.mention}.")
     

#--------------------------------------------------------------------------------------------------------------------------




@bot.tree.command(name="greet",description = "Sends a heartful Greeting!")
async def greet(interaction: discord.Interaction):
    username = interaction.user.mention
    await interaction.response.send_message(f"Hey there!, {username}")


#-------------------------------------------------------------------------------------------------------------------------
Song_queues = {}
Current_song = {}      
GID = 1466069152338018328

@bot.tree.command(name = "play", description="Play or add a song to the queue")
@app_commands.describe(
     song_query = "Search query"
)
async def play(interaction: discord.Interaction, song_query: str):
    await interaction.response.defer()

    vc = interaction.user.voice.channel

    if vc is None:
        await interaction.followup.send(f"{interaction.user.mention} You must be in a voice channel to play songs.")
        return
     
    voice_client = interaction.guild.voice_client

    if voice_client is None:
         voice_client = await vc.connect()
    elif voice_client != voice_client.channel:
         await voice_client.move_to(vc)

    # Check if it's a playlist link
    is_playlist = "playlist" in song_query.lower() or "youtube.com/playlist" in song_query or "youtu.be" in song_query
    
    yt_dlp = {
         "format": "bestaudio[abr<=320]/bestaudio",
         "noplaylist": not is_playlist,
         "youtube_include_dash_manifest": False,
         "youtube_include_hls_manifest": False,
    }

    # If it's a direct link, use it as is; otherwise search for it
    if song_query.startswith(("http://", "https://")):
        query = song_query
    else:
        query = "ytsearch1: " + song_query
    
    results = await search_ytdlp_async(query, ydl_opts=yt_dlp)
    
    # Handle both single track and playlist results
    if "entries" in results:
        tracks = results["entries"]
    else:
        tracks = [results]

    if len(tracks) == 0:
            await interaction.followup.send(f"{interaction.user.mention} No results found for {song_query}.")
            return
    
    guild_id = str(interaction.guild.id)
    if Song_queues.get(guild_id) is None:
         Song_queues[guild_id] = deque()

    # Add all tracks to queue
    added_count = 0
    track_titles = []
    for track in tracks:
        try:
            audio_url = track["url"]
            title = track.get("title", "Untitled")
            Song_queues[guild_id].append((audio_url, title))
            track_titles.append(title)
            added_count += 1
        except (KeyError, TypeError):
            continue

    if added_count == 0:
            await interaction.followup.send(f"{interaction.user.mention} No valid tracks found.")
            return

    if voice_client.is_playing() or voice_client.is_paused():
         if added_count == 1:
            await interaction.followup.send(f"{interaction.user.mention} Added to queue: **{track_titles[0]}**")
         else:
            await interaction.followup.send(f"{interaction.user.mention} Added **{added_count}** songs to queue.")
    else:
            title = track_titles[0]
            if added_count == 1:
                await interaction.followup.send(f"Now playing: **{title}**")
            else:
                await interaction.followup.send(f"Now playing: **{title}** + **{added_count - 1}** more songs from playlist")
            await play_next_song(voice_client, guild_id,interaction.channel)



@bot.tree.command(name="skip",description="Skips the current song")
async def skip(interaction: discord.Interaction):
     
     if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
          interaction.guild.voice_client.stop()
          await interaction.response.send_message(f"Skipped the current song.")
     else:
             
             await interaction.response.send_message(f"No song is currently playing.")


@bot.tree.command(name="pause",description="Pauses the current song")
async def pause(interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client is None or not voice_client.is_playing():
          await interaction.response.send_message(f"Nothing is playing.")
          return
        voice_client.pause()
        await interaction.response.send_message(f"Paused.")

@bot.tree.command(name="resume",description="Resumes the paused song")
async def resume(interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            await interaction.response.send_message(f"Im not in a voice channel.")
            return
        
        if not voice_client.is_paused():
            await interaction.response.send_message(f"The song is not paused.")
            return
        
        voice_client.resume()
        await interaction.response.send_message(f"Resumed the current song.")


@bot.tree.command(name="queue",description="Shows the queue of songs")
async def replay(interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        await interaction.response.defer()

        guild_id = str(interaction.guild.id)
        queue = Song_queues.get(guild_id, deque())
        queue_list = [f"**{i+1}.** {title}" for i, (_, title) in enumerate(queue)]
        if not queue_list:
            await interaction.followup.send(f"The current queue is empty.")
        else:
            await interaction.followup.send(f"The current queue is:\n{'\n'.join(queue_list)}")
        


@bot.tree.command(name="stop",description="Stops the music and clears the queue")
async def stop(interaction: discord.Interaction):
        await interaction.response.defer()
        voice_client = interaction.guild.voice_client
        
        if not voice_client or not voice_client.is_connected():
            await interaction.followup.send(f"Im not in a voice channel.")
            return
        
        guild_id = str(interaction.guild.id)
        if guild_id in Song_queues:
             Song_queues[guild_id].clear()


        if voice_client.is_playing() or voice_client.is_paused():
             voice_client.stop()

        
        await interaction.followup.send(f"Stopped the music and cleared the queue.")

        await voice_client.disconnect()

async def search_ytdlp_async(query,ydl_opts):
     loop = asyncio.get_running_loop()
     return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
         return ydl.extract_info(query, download=False)
     


async def play_next_song(voice_client, guild_id, channel):
    if guild_id in Song_queues and Song_queues[guild_id]:
          audio_url, song_title = Song_queues[guild_id].popleft()
          Current_song[guild_id] = song_title
          ffmpeg_opts = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -c:a libopus -b:a 320k",
          }
          source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_opts, executable="bin\\ffmpeg\\ffmpeg.exe")

          def after_play(error):
               if error:
                    print(f"Error: {error}")
               asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)

          voice_client.play(source, after=after_play)
          asyncio.create_task(channel.send(f"Now playing: **{song_title}**"))
    else:
            if guild_id in Current_song:
                del Current_song[guild_id]
            if voice_client.is_connected():
                await voice_client.disconnect()
            

@bot.tree.command(name="now", description="Shows the currently playing song")
async def now(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    guild_id = str(interaction.guild.id)
    
    if voice_client is None or not voice_client.is_connected():
        await interaction.response.send_message(f"The bot is not in a voice channel.")
        return
    
    if not (voice_client.is_playing() or voice_client.is_paused()):
        await interaction.response.send_message(f"No song is currently playing.")
        return
    
    if guild_id in Current_song:
        current_title = Current_song[guild_id]
        status = "⏸️ Paused" if voice_client.is_paused() else "▶️ Playing"
        await interaction.response.send_message(f"{status}: **{current_title}**")
    else:
        await interaction.response.send_message(f"No song information available.")



bot.run(TOKEN)
