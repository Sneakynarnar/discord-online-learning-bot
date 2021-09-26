import discord
from discord import File
from discord.ext import commands, tasks
import sqlite3
import random
import asyncio
import logging
import logging.handlers
import discord_slash
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from discord_slash import SlashCommand, cog_ext
import regex as re
import io
import json
from datetime import timedelta
from discord_slash.utils.manage_commands import create_option
from datetime import datetime
guild_ids = [836901717160886292, 883409165391896626,884796354390523974]
logger = logging.getLogger("bot")
con = sqlite3.connect("resources/databases/schooldata.db")
cur = con.cursor()

class Lessons(commands.Cog):
        def __init__(self, bot):
            self.bot   = bot
        

        class Lesson():
            def __init__(self, class_id, guild_id, dateTime, subject, teacher_id, repeatWeekly):
                self.id = class_id
                self.guild_id = guild_id
                self.dateTime = dateTime
                self.subject = subject
                self.teacher_id = teacher_id
                self.repeatWeekly = repeatWeekly
                self.students = []

        @commands.Cog.listener()
        async def on_ready(self):
            logger.debug("Homework cog is ready!")
        
        @cog_ext.cog_slash(name="addstudents", description="Adds students to a class", guild_ids=guild_ids, options = [
                                                                                                                create_option(name="student", description="A student to be added to the classd",required=True, option_type=6), 
                                                                                                                create_option(name="student1", description="A student to be added to the class",required=False, option_type=6),
                                                                                                                create_option(name="student2", description="A student to be added to the class",required=False, option_type=6),
                                                                                                                create_option(name="student3", description="A student to be added to the class",required=False, option_type=6),
                                                                                                                create_option(name="student4", description="A student to be added to the class",required=False, option_type=6),
                                                                                                                create_option(name="student5", description="A student to be added to the class",required=False, option_type=6)])
        async def addStudents(self, ctx: discord_slash.SlashContext, student, student1, student2, student3, student4, student5):
            pass
        
        @cog_ext.cog_slash(name="createlesson", description="Creates a lesson", guild_ids=guild_ids, options = [create_option(name="subject",description="The subject of the lesson", required=True, option_type=3), 
                                                                                                                create_option(name="time", description="The time of the event in the format DD/MM/YYYY HH:MM", required=True, option_type=3),
                                                                                                                create_option(name="repeat_weekly", description="Sets whether the lesson repeats this time and day every week", required=True, option_type=5)])   
        async def createLesson(self, ctx: discord_slash.SlashContext, subject, time, repeat_weekly):
            
            dateMatch = re.match("(\d{2})\/(\d{2})\/(\d{4}) (\d{2}):(\d{2})", time)
            if dateMatch:
                time = "" + dateMatch.group(3) + "-"+dateMatch.group(2) + "-" + dateMatch.group(1) + " " + dateMatch.group(4) + ":" + dateMatch.group(5) #putting the date in the right format

            else:
                await ctx.send("Incorrect syntax for time")
                return

            try:
                time = datetime.fromisoformat(time) # gets datetime object from ISO format string

            except Exception as e:
                print(e)
                await ctx.send("There is something wrong with the time you entered. Are you sure it's right?") # Error is most likely because of an invalid time
                return
            
            cur.execute("SELECT teacherRoleId FROM schoolGuilds WHERE guildID = ?", (ctx.guild.id, )) #Get the teacherRoleId
    
            roleId = cur.fetchone() # this will return a tuple with one value 
            roleId = roleId[0] # take the one value in the tuple
            role = ctx.guild.get_role(roleId) # get the role object from ID
            
            if role not in ctx.author.roles: # If the author doesnt have a teacher role he/she is not a teacher
                await ctx.send("Only teachers can create lessons! If you feel this is in error do /info to see the bot roles. Roles needed for the bot to work may have been deleted and/or replaced.")
                return

            
            newLesson = self.Lesson(self.generateId(), ctx.guild.id, time, subject, ctx.author.id, repeat_weekly) # Creating a lesoon object
            print(newLesson)
            cur.execute("INSERT INTO lessons VALUES (?,?,?,?,?,?)", (newLesson.id, newLesson.guild_id, newLesson.dateTime, newLessons.subject, newLesson.teacher_id, newLesson.repeat_weekly))
            print("Got this far")
            con.commit()

        def generateId(self):
            while True: 
                lessonId = random.randint(0, 100000000000000)
                cur.execute("SELECT * FROM lessons WHERE classId = ?", (lessonId,))

                if cur.fetchone is None:
                    return lessonId
                else:
                    continue

def setup(bot):
    bot.add_cog(Lessons(bot))
