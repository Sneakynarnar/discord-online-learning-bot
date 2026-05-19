import sqlite3
import discord
from discord.ext import commands
import logging
import discord_slash
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_slash.utils.manage_components import create_actionrow, create_button, wait_for_component
from discord_slash.model import ButtonStyle
from discord_slash import cog_ext, context
import random
import asyncio
import regex as re

logger = logging.getLogger("bot")

GUILD_IDS = [836901717160886292, 884796354390523974, 899703139840708668]


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bannedWords = ["homework"]
        self.con = sqlite3.connect("resources/databases/schooldata.db")
        self.cur = self.con.cursor()

    @commands.Cog.listener()
    async def on_ready(self):
        logger.debug("Commands cog is ready!")

    @commands.Cog.listener()
    async def on_message(self, message):
        content = message.content
        content_lower = content.lower()
        for banned_word in self.bannedWords:
            if banned_word in content_lower:
                self.cur.execute(
                    "SELECT managerChatId FROM schoolGuilds WHERE guildID = ?",
                    (message.guild.id,)
                )
                record = self.cur.fetchone()
                channel = message.guild.get_channel(record[0])
                await channel.send(embed=discord.Embed(
                    title=f"Deleted message by {message.author.display_name}",
                    description=f"**Message:** {content}"
                ))
                await message.delete()
                return

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild

        async def wait_for_name():
            def check(m):
                name = m.content
                name_match = re.match(r"(\w+ \w+)", name)
                has_banned = any(w in name.lower() for w in self.bannedWords)
                return (
                    m.author == member
                    and m.channel == member.dm_channel
                    and name_match
                    and not has_banned
                )
            try:
                return await self.bot.wait_for('message', timeout=120, check=check)
            except asyncio.TimeoutError:
                return None

        self.cur.execute(
            "SELECT studentRoleId, managerChatId FROM schoolGuilds WHERE guildID = ?",
            (member.guild.id,)
        )
        record = self.cur.fetchone()
        if record is None:
            return

        student_role = member.guild.get_role(record[0])
        manager_chat = guild.get_channel(record[1])

        await member.create_dm()
        await member.dm_channel.send(
            "What is your name (first and last name)? You must respond within 2 minutes "
            "or you will be kicked. Fake or troll names will be punished. "
            "The bot will only accept valid names (no special characters)."
        )

        message = await wait_for_name()
        if message is None:
            await member.kick()
            return

        name = message.content
        await member.dm_channel.send(f"Hi {name}, you will be granted access when approved by an admin!")

        actionrow = create_actionrow(
            create_button(style=ButtonStyle.green, label="Accept Member", custom_id="confirm"),
            create_button(style=ButtonStyle.red, label="Decline Member", custom_id="decline"),
        )
        embed = discord.Embed(
            description=f"Member {member.mention} wants to join as **{name}**. "
                        f"Account created: {member.created_at}"
        )
        embed.set_thumbnail(url=member.avatar_url)
        await manager_chat.send(embed=embed, components=[actionrow])

        button_ctx = await wait_for_component(self.bot, components=actionrow)
        if button_ctx.custom_id == "confirm":
            await member.edit(nickname=name)
            await member.add_roles(student_role)
            await button_ctx.send(f"{name} confirmed by {button_ctx.author.name}")
            await member.dm_channel.send(f"You have been confirmed by {button_ctx.author.name}!")
        else:
            await member.kick()
            await manager_chat.send(f"{name} rejected by {button_ctx.author.name}")

    @cog_ext.cog_slash(name="ping", description="Pong!", guild_ids=GUILD_IDS)
    async def ping(self, ctx: discord_slash.context):
        await ctx.send("Pong! ({0:.1f}ms)".format(self.bot.latency * 1000))

    @cog_ext.cog_slash(
        name="report", description="Report someone who is breaking the rules!",
        guild_ids=GUILD_IDS,
        options=[
            create_option(name="member", description="Member to report", required=True, option_type=6),
            create_option(name="reason", description="Reason for the report", required=True, option_type=3),
        ]
    )
    async def report_command(self, ctx: discord_slash.SlashContext, member, reason):
        self.cur.execute(
            "SELECT managerChatId FROM schoolGuilds WHERE guildID = ?", (ctx.guild.id,)
        )
        record = self.cur.fetchone()
        manager_channel = ctx.guild.get_channel(record[0])
        await ctx.send("Report sent.")
        await manager_channel.send(embed=discord.Embed(
            title="Report",
            description=f"{ctx.author.mention} has reported {member.mention}\nReason: {reason}"
        ))

    @cog_ext.cog_slash(
        name="rockpaperscissors", guild_ids=GUILD_IDS,
        options=[create_option(
            name="choice", description="Rock, paper, or scissors?",
            required=True, option_type=3,
            choices=[
                create_choice(name="rock", value="rock"),
                create_choice(name="paper", value="paper"),
                create_choice(name="scissors", value="scissors"),
            ]
        )]
    )
    async def rps_command(self, ctx: discord_slash.SlashContext, choice):
        choices = ["rock", "paper", "scissors"]
        if choice not in choices:
            await ctx.send("That is not a valid choice.")
            return

        ai_choice = random.choice(choices)
        wins = {("paper", "rock"), ("rock", "scissors"), ("scissors", "paper")}

        if (choice, ai_choice) in wins:
            await ctx.send(f"You picked {choice} and I picked {ai_choice} — you win!")
        elif choice == ai_choice:
            await ctx.send(f"We both picked {choice}! It's a draw!")
        else:
            await ctx.send(f"You picked {choice} and I picked {ai_choice} — I win!")


def setup(bot):
    bot.add_cog(Commands(bot))
