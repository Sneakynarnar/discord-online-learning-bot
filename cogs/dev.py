import discord
from discord.ext import commands, tasks
import logging
import sqlite3 
import logging.handlers
import discord_slash
from discord_slash import SlashCommand, cog_ext, context
import asyncio
from discord_slash.utils.manage_commands import create_option
con = sqlite3.connect("resources/databases/schooldata.db")
cur = con.cursor()
logger = logging.getLogger("bot")
guild_ids = [836901717160886292,884796354390523974,899703139840708668]
owner = 339866237922181121
class Dev(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
        
        @commands.Cog.listener()
        async def on_ready(self):
            logger.debug("Dev cog is ready!")
        @cog_ext.cog_slash(name="delchannels", guild_ids=guild_ids, options= [create_option(name="categoryid", description="Specify a categoryId",option_type=3, required=False)])
        async def delChannels(self,ctx, categoryid=None):
            await ctx.defer()
            if categoryid is not None:
                for channel in self.bot.get_channel(int(categoryid)).channels:
                    await channel.delete()
                    await asyncio.sleep(0.2)
            else:
                if ctx.author == ctx.guild.get_member(owner):
                    
                    for channel in ctx.guild.channels:
                        

                        if channel.name != ctx.channel.name:
                            await channel.delete()
                            await asyncio.sleep(0.2)

                            
                    
                    for role in ctx.guild.roles:
                        try:
                            await role.delete()
                        except:
                            continue
                    await ctx.send("Channels deleted!")
        @commands.command(name="deletedata", hidden=True)
        async def deleteData(self, ctx, guildId: int):
            if ctx.author == ctx.guild.get_member(owner):
                
                if type(guildId) is not int:
                    await ctx.send("That is not an integer!")
                    return
                cur.execute("SELECT * FROM schoolGuilds WHERE guildID =:guildId", {"guildId": guildId})
                records = cur.fetchall()
                print(records)
                if len(records) == 0:
                    await ctx.send(f"No records found with guild ID {guildId}")
                else:
                    cur.execute("DELETE FROM schoolGuilds WHERE guildID = :guildId", {"guildId": guildId})
                    con.commit()
                    await ctx.send("Deleted.")



def setup(bot):
    bot.add_cog(Dev(bot))
