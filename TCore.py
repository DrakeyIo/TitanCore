import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import sqlite3
from datetime import timedelta



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

intents = discord.Intents.default()  #config for permissions
intents.message_content = True    #enables reading and handling messages


bot = commands.Bot(command_prefix=".", intents=intents)




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
    if msg.author.id != bot.user.id:  #to make sure the bot only reads user msgs and not its own messages.
        await msg.channel.send(f"Interesting.")


    await bot.process_commands(msg)

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

#----------------------------------------------------------------------


@bot.tree.command(name="warn",description = "warns a user")
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
         await interaction.response.send_message(f"⚠️{member.mention} has been warned. {numwarns} Warnings.")


#----------------------------------------------------------------------------------------------------------------


@bot.tree.command(name="clearwarn",description="clears all warnings from given user")
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
        conn = sqlite3.connect(f"{BASE_DIR}\\user_warns.db")
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT WarnCnt FROM upg
                       WHERE (uid = ?) AND (gid = ?);""",
                    (member.id,interaction.guild.id))
        
        result = cursor.fetchone()
        conn.close()
        if (result[0] == 1):
            await interaction.response.send_message(f"{member.mention} has {result[0]} Warning.")
        else:
              await interaction.response.send_message(f"{member.mention} has {result[0]} Warnings.")



@bot.tree.command(name="greet",description = "Sends a heartful Greeting!")
async def greet(interaction: discord.Interaction):
    username = interaction.user.mention
    await interaction.response.send_message(f"Hey there!, {username}")



bot.run(TOKEN)