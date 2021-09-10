import discord
from discord.ext import commands, tasks
import logging
import logging.handlers
from discord_slash import SlashCommand
import json
logger = logging.getLogger("bot")


class Utility(commands.Cog):
        def __init__(self, bot):
            self.bot = bot


        @commands.Cog.listener()
        async def on_ready(self):
            logger.debug("Utility cog is ready!")
        



def setup(bot):
    bot.add_cog(Utility(bot))