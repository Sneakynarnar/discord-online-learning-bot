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
        
        def generateId(self):
            while True: 
                lessonId = random.randint(0, 100000000000000)
                cur.execute("SELECT * FROM lessons WHERE classId = ?", (lessonId,))

                if cur.fetchone() is None:
                    return lessonId
                else:
                    print(cur.fetchone())
                    continue
        class Lesson():

            def __init__(self, payload):
                
                self.id = payload[0]
                self.guild_id = payload[1]
                self.name = payload[2]
                self.dateTime = payload[3]
                self.subject = payload[4]
                self.teacher_id = payload[5]
                self.repeatWeekly = payload[6]
                self.description = payload[7]
                self.students = []
                

        @commands.Cog.listener()
        async def on_ready(self):
            logger.debug("Lessons cog is ready!")
        async def waitForMessage():
            def check(m):
                return m.author == ctx.author and m.channel == ctx.author.dm_channel
            try:             
                message = await self.bot.wait_for('message', timeout=300, check=check)
            except asyncio.TimeoutError:
                await ctx.author.dm_channel.send("Timed out.")
            return message.content       
        @cog_ext.cog_slash(name="lessoninfo", description="Displays lesson info", guild_ids=guild_ids, options = [create_option(name="name", description="The name of the lesson. Do /listlessons to see your lessons",required=True,option_type=3)])
        async def lessonInfo(self,ctx, name):

            name = name.lower()
            
            cur.execute("SELECT * FROM lessons WHERE guildId = ? AND LOWER(name) = ? ", (ctx.guild.id, name))
            lesson = self.Lesson(cur.fetchone())
            time = datetime.fromisoformat(lesson.dateTime)

            if lesson.repeatWeekly:
                format = "Repeats every %A @ %I:%M %p"
                time = time.strftime(format)
            else:
                format = "Lesson is at %A %d/%m/%y"
                time = time.strftime(format)

            info =f"**{lesson.subject}**\nDescription: {lesson.description}\n\nTime: {time}"
            embed = discord.Embed(title=lesson.name, description=info)
            teacher = ctx.guild.get_member(lesson.teacher_id)
            embed.add_field(name="Teacher", value=f"{teacher.mention}")
            cur.execute("SELECT studentId FROM studentLessons WHERE classId = ?", (lesson.id,))
            records = cur.fetchall()
            members = [ [ctx.guild.get_member(x[0]).name, ctx.guild.get_member(x[0])] for x in records]
            def take_second(elem):
                return elem[0]
            members = sorted(members, key=take_second)
            ROWS = 2

            rem = len(members) % ROWS
            if rem == 0:
                columns = int((len(members) /ROWS))
            else:
                columns = int((len(members)//ROWS) + 1)
            students = ""
            members.sort()
            total = 0
            for name in members:
                maxLength = len(name) #getting the longest name
                total+= len(name)

            averageLength= total/ len(members)
            upperQuartile = (maxLength + averageLength) / 2
            totalCharacters = upperQuartile + 12

            for x in range(ROWS):
                studentrow = ""
                for y in range(columns):
                    index =x+(ROWS*y)

                    
                    if index > len(members)-1:
                        break
                    name = members[index][0]
                    member = members[index][1]
                    spaces = int(totalCharacters - len(name))
                    whitespace = ""
                    whitespace += " "*spaces

                    studentrow+= member.mention+whitespace
                students += studentrow + "\n"


            embed.add_field(name="Students", value=students, inline=False)

            await ctx.send(embed=embed)
             
        @cog_ext.cog_slash(name="listlessons", description="Lists your lessons!", guild_ids=guild_ids, options = [create_option(name="page", description="The page of lessons you want to see",required=False, option_type=4)])
        async def listLessonsCommand(self, ctx, page=None):
            page = 1 if page is None else page
            cur.execute("SELECT teacherRoleId, studentRoleId FROM schoolGuilds WHERE guildID = ? ", (ctx.guild.id,))
            record = cur.fetchone() # fetches the one (and only) record
            teacher = ctx.guild.get_role(record[0])  # Gets the role objects
            student = ctx.guild.get_role(record[1])
            if teacher in ctx.author.roles:
                cur.execute("SELECT * FROM lessons WHERE teacherId = ?", (ctx.author.id,))
                records = cur.fetchall()
            elif student in ctx.author.roles:
                cur.execute("SELECT classId FROM studentLessons WHERE guildId = ? AND studentId = ?",(ctx.guild.id, ctx.author.id))
                records = cur.fetchall()
                ids = [x[0] for x in records]
                records = []
                for id in ids:
                    cur.execute("SELECT * FROM lessons WHERE classId = ?", (id,))
                    records.append(cur.fetchone())
            else:
                await ctx.send("You don't have a student or a teacher role? Hmm that's weird. You should have got one when you joined. Ask the managers.")
                return
            if len(records) == 0 :
                await ctx.send("You have no lessons. To create lessons do /createlesson")
                return

            embed = await self.listLessons(records, page)
            if embed is None:
                await ctx.send("This page does not exist")
                return
            await ctx.send(embed=embed)
        @cog_ext.cog_slash(name="addstudents", description="Adds students to a class", guild_ids=guild_ids, options = [
                                                                                                                create_option(name="class_name", description="The name of the lesson. Do /listlessons if you aren't sure", required=True, option_type=3),
                                                                                                                create_option(name="student", description="A student to be added to the class",required=True, option_type=6), 
                                                                                                                create_option(name="student1", description="A student to be added to the class",required=False, option_type=6),
                                                                                                                create_option(name="student2", description="A student to be added to the class",required=False, option_type=6),
                                                                                                                create_option(name="student3", description="A student to be added to the class",required=False, option_type=6),
                                                                                                                create_option(name="student4", description="A student to be added to the class",required=False, option_type=6),
                                                                                                                create_option(name="student5", description="A student to be added to the class",required=False, option_type=6)])
        async def addStudents(self, ctx: discord_slash.SlashContext, class_name, student, student1=None, student2=None, student3=None, student4=None, student5=None):
            students = [student, student1, student2, student3, student4, student5]
            cur.execute("SELECT * FROM lessons WHERE teacherId = ? AND name = ?", (ctx.author.id, class_name))
            record = cur.fetchone()
            print(record)
            if record is None:
                await ctx.send("You have no classes with that name! To see your lessons do /listlessons or to create a new one do /createlesson")
                return
            
            
            lesson = self.Lesson(record)
            for student in students:
                if student is not None:
                    cur.execute("INSERT INTO studentLessons VALUES (?,?,?)", (student.id, lesson.id, ctx.guild.id))
            
            await ctx.send("All students have beeen added run the command to add more!")
            con.commit()
        
        @cog_ext.cog_slash(name="createlesson", description="Creates a lesson", guild_ids=guild_ids, options = [create_option(name="name",description="The name of the Lesson (must be unique)", required=True, option_type=3),
                                                                                                                create_option(name="subject",description="The subject of the lesson", required=True, option_type=3), 
                                                                                                                create_option(name="time", description="The time of the event in the format DD/MM/YYYY HH:MM", required=True, option_type=3),
                                                                                                                create_option(name="repeat_weekly", description="Sets whether the lesson repeats this time and day every week", required=True, option_type=5),
                                                                                                                create_option(name="description", description="Anything you want to say about the lesson", required=True, option_type=3)])   
        async def createLesson(self, ctx: discord_slash.SlashContext, name, subject, time, repeat_weekly, description):
            
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
            cur.execute("SELECT * FROM lessons WHERE teacherId = ? AND LOWER(name) = ?", (ctx.author.id, name.lower()))
            if cur.fetchone() is not None:
                await ctx.send(f"You already have a class named {name}!")
                return
            cur.execute("SELECT teacherRoleId FROM schoolGuilds WHERE guildID = ?", (ctx.guild.id, )) #Get the teacherRoleId
    
            roleId = cur.fetchone() # this will return a tuple with one value 
            roleId = roleId[0] # take the one value in the tuple
            role = ctx.guild.get_role(roleId) # get the role object from ID
            
            if role not in ctx.author.roles: # If the author doesnt have a teacher role he/she is not a teacher
                await ctx.send("Only teachers can create lessons! If you feel this is in error do /info to see the bot roles. Roles needed for the bot to work may have been deleted and/or replaced.")
                return  


            payload =(self.generateId(), ctx.guild.id, name, time, subject, ctx.author.id, repeat_weekly, description)
            newLesson = self.Lesson(payload) # Creating a lesoon object
           
            cur.execute("INSERT INTO lessons VALUES (?,?,?,?,?,?,?,?)", payload)
            con.commit()
            await ctx.send(f"Created new {newLesson.subject} lesson at {newLesson.dateTime}!")

        async def listLessons(self, lessons, page):


            total = len(lessons)
            
            lastPage = total % 8 # divide by how many terms we want in our embed and throw away the remainder
            if lastPage == 0:
                lastPage = int(total / 8) # If its divisible by 8 then the last page will be full 
            else:
                lastPage = int((total // 8) + 1) # if not we would need an extra page for the remaining lessons  
        
            if page >= 1 and page <= lastPage:
                embed = discord.Embed(
                    title="Your lessons!",
                    description="These are all of your lessons:",
                )
                text = "page {0}/{1}".format(page, lastPage)
                embed.set_footer(text=text)
                counter = 1
                for lesson in lessons:
                    lesson = self.Lesson(lesson)
                    if counter > (8 * (page - 1)) and counter < ((page * 8)+1):
                        time = datetime.fromisoformat(lesson.dateTime)
                        if lesson.repeatWeekly:
                            format = "%A @ %I:%M %p"
                            
                            time = time.strftime(format)
                            embed.add_field(name=lesson.name, value=f"Subject: {lesson.subject}\nRepeats every week {time}", inline=False)
                        else:
                            format = "%A %d/%m/%y"
                            time = time.strftime(format)
                            embed.add_field(name=lesson.name, value=f"Subject: {lesson.subject}\nLesson is at {time}", inline=False)                            

            
                    counter += 1
                
                return embed
            else:
                return None


def setup(bot):
    bot.add_cog(Lessons(bot))
