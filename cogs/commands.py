import discord
from discord.ext import commands, tasks
import logging
import logging.handlers
import discord_slash
from discord_slash import SlashCommand, cog_ext, context

logger = logging.getLogger("bot") # Getting the logger

guild_ids = [836901717160886292,884796354390523974]
class Commands(commands.Cog):
        def __init__(self, bot):
            self.bot = bot ### initial
        @commands.Cog.listener()
        async def on_ready(self):
            logger.debug("Commands cog is ready!")
        

        @cog_ext.cog_slash(name="ping", description="Pong!", guild_ids =guild_ids)
        async def ping(self, ctx: discord_slash.context):
            await ctx.send("Pong! ({0:1f}ms)".format(self.bot.latency*1000))


def setup(bot):
    bot.add_cog(Commands(bot))
