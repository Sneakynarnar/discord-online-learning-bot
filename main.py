import configparser as cp
import discord
import os
import logging
import logging.handlers
from discord.ext import commands
from discord_slash import SlashCommand
from dotenv import load_dotenv

load_dotenv()


def setup_logging():
    logger = logging.getLogger('bot')
    logger.setLevel(logging.DEBUG)
    handler = logging.handlers.TimedRotatingFileHandler(
        filename="resources/logs/bot.log", when="h", interval=8,
        backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
    logger.addHandler(handler)


def load_extensions(bot, config):
    logger = logging.getLogger('bot')
    logger.debug("========================RESTART===========================")
    for ext in config["cogs"]:
        try:
            bot.load_extension("cogs." + ext)
        except Exception as e:
            logger.debug(f"Error loading {ext}: {e}")
    logger.debug("Cogs loaded")


def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN environment variable not set")

    intents = discord.Intents.all()
    bot = commands.Bot(intents=intents, help_command=None, command_prefix="?>")
    SlashCommand(bot, sync_commands=True)

    config = cp.ConfigParser()
    config.read("resources/cogs.ini")

    @bot.event
    async def on_message(msg):
        try:
            await bot.process_commands(msg)
        except Exception as e:
            print(f"Error processing commands: {e}")

    setup_logging()
    load_extensions(bot, config)
    print("Bot running...")
    bot.run(token)


if __name__ == "__main__":
    main()
