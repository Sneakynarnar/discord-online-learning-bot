import sqlite3
import discord
from discord.ext import commands, tasks
import logging
import logging.handlers
import discord_slash
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_slash.utils.manage_components import create_actionrow, create_button, wait_for_component
from discord_slash.model import SlashCommandPermissionType, ButtonStyle
from discord_slash import SlashCommand, cog_ext, context
import random
import asyncio
logger = logging.getLogger("bot") # Getting the logger
con = sqlite3.connect("resources/databases/schooldata.db")
cur = con.cursor()
guild_ids = [836901717160886292,884796354390523974,899703139840708668,]
class Commands(commands.Cog):
        def __init__(self, bot):
            self.bot = bot ### initial
            self.bannedWords = ["english"]
        @commands.Cog.listener()
        async def on_ready(self):
            logger.debug("Commands cog is ready!")
        
        @commands.Cog.listener()
        async def on_member_join(self, member):
            guild = member.guild
            async def waitForMessage():
                def check(m):
                    name = message.content()
                    validCharacters = "abcdefghijklmnopqrstuvwxyz-\" " 
                    valid = True
                    for char in name:
                        if char not in validCharacters:
                            valid =False
                    nameMatch = re.match(name, "(\D+ \D+)") # Matching for two words IE Nana Adjei
                    bannedCheck = True
                    for word in bannedWords: # check for banned words in the name
                        if word in name:
                            bannedCheck = False
                    return m.author == member and m.channel == member.dm_channel and valid and nameMatch and bannedCheck # if all checks are passed we take take the message
                try:
                    message = await self.bot.wait_for('message', timeout=120, check=check) # wait for message for 120 seconds and check must return true
                except asyncio.TimeoutError:
                    return None
                return message
            cur.execute("SELECT studentRoleId, managerChatId FROM schoolGuilds WHERE guildID = ?", (member.guild.id,)) # getting the student role and manager chat
            record = cur.fetchone()  
            if record is None:
                return
            studentRole = member.guild.get_role(record[0]) # getting role objects from ids
            managerChat = guild.get_channel(record[1])    
            await member.create_dm()
            await member.dm_channel.send("What is your name (First and last Name). You must respond within 2 minutes or you will be kicked, your teachers will know what name you entered and fake/troll names will be punished.\
                the bot will only respond to valid names (No special characters)")
            message = await waitForMessage()
            if message is None:
                await member.kick()
            else:
                name = message.content()
                actionrow = create_actionrow(
                create_button(style=ButtonStyle.green, label="Accept Member", custom_id="confirm"),
                create_button(style=ButtonStyle.red, label="Decline Member", custom_id="decline", )) # Accept and decline button 
                embed = discord.Embed(name="Member wants to join", description=f"Member {member.mention} wants to join as {name}, the account was created at {member.created_at}",)
                embed.set_thumbnail(url=member.avatar_url)
                message = await managerChat.send(embed=embed, actionrow=[actionrow])       
                buttonCtx: ComponentContext = await wait_for_component(self.bot, components=actionrow)
                if buttonCtx.custom_id == "confirm":
                    await member.edit(nickname=name)
                    await member.add_role(studentRole)
                    await managerChat.send(f"{name} confirmed by {buttonCtx.author.name}")

                else:
                    await member.kick()
                    await managerChat.send(f"{name} rejected by {buttonCtx.author.name}")

                

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
            if (aiChoice == "rock" and choice=="paper") or (aiChoice== "scissors" and choice=="rock") or (aiChoice=="paper" and choice=="scissors"):
                await ctx.send(f"You picked {choice} and I picked {aiChoice} so I lose :(")
            elif choice == aiChoice:
                await ctx.send(f"We both picked {choice}! So its a draw! We are so connected <3")

            else:
                await ctx.send(f"You picked {choice} and I picked {aiChoice} so I win ;)")


def setup(bot):
    bot.add_cog(Commands(bot))
