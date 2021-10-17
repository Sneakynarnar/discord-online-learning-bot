import discord
from discord.ext import commands, tasks
import logging
import logging.handlers
import discord_slash
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_slash import SlashCommand, cog_ext, context
import random
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

        @cog_ext.cog_slash(name="ban", guild_ids=guild_ids, options = [create_option(  	
                                            name = "member", # name of the option that will be displayed
                                            description="Member to ban", # The description of what the option does
                                            required=True, # Whether the argument is required
                                            option_type=6, # The option type (6 means member)
                                            )])
        async def banCommand(self, ctx: discord_slash.SlashContext, member):
            await member.ban()
            await ctx.send(f"{member.name} has been banned.")


        @cog_ext.cog_slash(name="rockpaperscissors",guild_ids=guild_ids, options = [create_option(
                                        name= "choice",
                                        description="Rock paper or scisors?",
                                        required=True,
                                        option_type=3, 
                                        choices = [create_choice(name="rock", value="rock"),
                                                create_choice(name="paper", value="paper"),
                                                create_choice(name="scissors", value="scissors"),]
        )])
        async def rpsCommand(self, ctx: discord_slash.SlashContext, choice):
            choice = choice.lower()
            choices = ["rock", "paper", "scissors"]
            if choice not in choice:
                await ctx.send("That is not a valid choice.")
                return
            

            aiChoice = random.choice(choices)
            if (aiChoice == "Rock" and choice=="Paper") or (aiChoice== "Scissors" and choice=="Rock") or (aiChoice=="Paper" and choice=="Scissors"):
                await ctx.send(f"You picked {choice} and I picked {aiChoice} so I lose :(")
            elif choice == aiChoice:
                await ctx.send(f"We both picked {choice}! So its a draw! We are so connected <3")

            else:
                await ctx.send(f"You picked {choice} and I picked {aiChoice} so I win ;)")


def setup(bot):
    bot.add_cog(Commands(bot))
