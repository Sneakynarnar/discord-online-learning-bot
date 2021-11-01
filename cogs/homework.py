import discord
from discord.ext import commands, tasks
import logging
import logging.handlers
from discord_slash import SlashCommand


logger = logging.getLogger("bot")


class Homework(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
        
        @commands.Cog.listener()
        async def on_ready(self):
            logger.debug("Homework cog is ready!")
        






def setup(bot):
    bot.add_cog(Homework(bot))
