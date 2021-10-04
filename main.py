################# Main.py#####################
import configparser as cp
import discord
import json
import asyncio
import os
import sys
from datetime import datetime
from discord.ext import commands, tasks
from discord_slash import SlashCommand
from discord import Embed
from dotenv import load_dotenv
import subprocess
import logging
import logging.handlers
import sqlite3

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.all()
bot = commands.Bot(intents=intents, help_command=None, command_prefix="?>")
slash = SlashCommand(bot, sync_commands=True)
config = cp.ConfigParser()
config.read("resources/cogs.ini")



def setupLogging():
    logger = logging.getLogger('bot')
    logger.setLevel(logging.DEBUG)
    handler = logging.handlers.TimedRotatingFileHandler(filename="resources/logs/bot.log", when="h", interval=8, backupCount=3,encoding = "utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
    logger.addHandler(handler)

@bot.event
async def on_message(msg):
    try:
        await bot.process_commands(msg) #This is so when a message is sent in the server the bot can process if its a command or not
    except Exception as e:
        print(f"Error proccessing commands: {e}")




 
 

    

def loadExtentions():
    logger = logging.getLogger('bot')
    logger.debug("========================RESTART===========================")
    extentions = config["cogs"]
    for ext in extentions:
        try:
            cog = "cogs." + ext
            bot.load_extension(cog)
        except Exception as e:
            logger.debug(f"Error loading {ext} Exception: {e}") 
    logger.debug("Cogs Loaded")
    

setupLogging()
loadExtentions()
print("Bot Running...")
bot.run(TOKEN)