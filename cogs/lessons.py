import discord
import asyncio
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
#This is a change
class Lessons(commands.Cog):
        def __init__(self, bot):
            self.bot   = bot
            self.activeLessons = {}

        def get_lesson(self, id): # Returns the Lesson object from an ID
            cur.execute("SELECT * FROM lessons WHERE classId = ?", (id,))
            return self.Lesson(cur.fetchone(), self.bot)
        def generateId(self):
            while True: 
                lessonId = random.randint(100000000000000, 9999999999999999)
                cur.execute("SELECT * FROM lessons WHERE classId = ?", (lessonId,))

                if cur.fetchone() is None:
                    return lessonId
                else:
                    print(cur.fetchone())
                    continue
        class Lesson():

            def __init__(self, payload, bot):
                self.bot = bot
                self.id = payload[0]
                self.guild = bot.get_guild(payload[1])
                self.name = payload[2]
                self.dateTime = payload[3]
                self.subject = payload[4]
                self.teacher = self.guild.get_member(payload[5])
                self.repeatWeekly = payload[6]
                self.description = payload[7]
                self.lessonDuration = payload[8]
                self.vc = payload[9] # voice chat
                self.tc = payload[10] # text chat
                self.embedMessage = payload[11]
    
            def fetch_students(self):
                cur.execute("SELECT studentId FROM studentLessons WHERE classId = ? AND guildId = ?", (self.id, self.guild.id))
                records = cur.fetchall()
                students = [self.guild.get_member(x[0]) for x in records]
                return students
            
            async def start(self):

                students = self.fetch_students()

                cur.execute("SELECT activeLessonsCategoryId, waitingRoomId FROM schoolGuilds WHERE guildID = ?", (self.guild.id,))
                records = cur.fetchone()
                activeLessonCat = self.guild.get_channel(records[0])
                waitingRoom = self.guild.get_channel(records[1])

                
                role = await self.guild.create_role(name=self.name)
                overwrites = {
                    self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    role: discord.PermissionOverwrite(read_messages=True)
                }
                self.vc = await activeLessonCat.create_voice_channel(name=self.name, overwrites=overwrites)
                
                self.tc = await activeLessonCat.create_text_channel(name=self.name+"-text", overwrites=overwrites)
                embed = discord.Embed(title=f"Your {self.subject} lesson is starting now!", description=f"{self.name} is starting now!" )
                embed.add_field(name="Voice channel", value=f"Join the voice channel by clicking this link > {self.vc.mention}")
                embed.add_field(name="Text channel", value=f"View the text channel by clicking this > {self.tc.mention}\n\n**TIP:** If you join {waitingRoom.mention} then you will automatically get moved into your lesson when it starts!")
                infoEmbed = discord.Embed(title="Lesson Info", description=f"This lesson is being taught by {self.teacher.mention}")
                notJoinedStudents = students
                joinedStudents = []
                cur.execute("UPDATE lessons SET VC = ?, TC = ?,WHERE classId = ?", (self.vc.id,self.tc.id,message.id, self.id)) # Fixing the database showing all these as NONE
                con.commit()

                for student in students:
                    await student.add_roles(role)
                    await student.create_dm()
                    await student.dm_channel.send(embed=embed)
                if self.teacher in waitingRoom.members:
                    await self.teacher.move_to(self.vc) 
                    await self.teacher.add_roles(role)
                    await self.teacher.create_dm()
                    await self.teacher.dm_channel.send(embed=embed)
                for member in waitingRoom.members:
                    if member in notJoinedStudents:
                        await member.move_to(self.vc)
                        notJoinedStudents.remove(member)
                        joinedStudents.append(member)

                students = ""
                for student in notJoinedStudents:
                    students += f"{student.mention}\n"
                joinedStudentsStr = ""
                for student in joinedStudents:
                    joinedStudentsStr +=f"{student.mention}\n"
                
                joinedStudentsStr = "No students have joined yet" if len(joinedStudents) == 0 else joinedStudentsStr
                infoEmbed.add_field(name="Students who have joined", value=joinedStudentsStr,inline=False)
                infoEmbed.add_field(name="Students who haven't joined",value=students, inline=False)             

                message = await self.tc.send(embed=infoEmbed)

                print("got this far")
                await asyncio.sleep((self.lessonDuration+5)*60)
                self.vc.delete()
                self.tc.delete()
                cur.execute("DELETE FROM lessons WHERE classId = ?", (self.id,))
                for student in students:
                    await student.remove_roles(role)
                con.commit()
                
                
        @commands.Cog.listener()
        async def on_voice_state_update(self, member, before, after):
            if not (after.deaf or after.mute or after.self_deaf or after.self_mute or after.self_stream or after.self_video) :
                cur.execute("SELECT activeLessonsCategoryId FROM schoolGuilds WHERE guildID = ?", (member.guild.id,))
                activeLessonsCat = cur.fetchone()
                activeLessonsCat = member.guild.get_channel(activeLessonsCat[0])
                if after.channel in activeLessonsCat.channels or before.channel in activeLessonsCat.channels:
                    if after.channel in activeLessonsCat.channels:
                        lessonChannel = after.channel
                    elif before.channel in activeLessonsCat.channels:
                        lessonChannel = before.channel

                    cur.execute("SELECT * FROM lessons WHERE VC = ?", (lessonChannel.id,))
                    payload = cur.fetchone()
                    lesson = self.Lesson(payload, self.bot)
                    message =await lesson.tc.fetch_message(lesson.embedMessage)
                    embed = message.embed
                    notJoinedStudents = lessons.fetch_students()

                    joinedStudents = lesson.vc.members

                    joinedStudents.remove(lesson.teacher)

                    for student in notJoinedStudents:
                        if student in joinedStudents:
                            notJoinedStudents.remove(student)
                    

                        embed.set_field_at(3, name="Students Who have joined", value=self.formatMembers(joinedStudents))
                        embed.set_field_at(4, name="Students Who haven't joined", value=self.formatMembers(notJoinedStudents))

                    if before.channel in activeLessonsCat.channels:
                        l
                        await lesson.teacher.create_dm
                        await lesson.teacher.dm_channel.send(f"{member.nick} just left the call!")
                        await lesson.tc.send(f"{member.nick} just left the call!")
                    
                    return






        @commands.Cog.listener()
        async def on_ready(self):
            logger.debug("Lessons cog is ready!")
            self.checkForLesson.start()
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
            lesson = self.Lesson(cur.fetchone(), self.bot)
            time = datetime.fromisoformat(lesson.dateTime)

            if lesson.repeatWeekly:
                format = "Repeats every %A @ %I:%M %p"
                time = time.strftime(format)
            else:
                format = "Lesson is at %A %d/%m/%y"
                time = time.strftime(format)

            info =f"**{lesson.subject}**\nDescription: {lesson.description}\n\nTime: {time}"
            embed = discord.Embed(title=lesson.name, description=info)
            teacher = lesson.teacher
            embed.add_field(name="Teacher", value=f"{teacher.mention}")
            cur.execute("SELECT studentId FROM studentLessons WHERE classId = ?", (lesson.id,))
            records = cur.fetchall()
            members = [ [ctx.guild.get_member(x[0]).name, ctx.guild.get_member(x[0])] for x in records]
            students = await self.formatMembers(members)


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
        
            if record is None:
                await ctx.send("You have no classes with that name! To see your lessons do /listlessons or to create a new one do /createlesson")
                return
            
            
            lesson = self.Lesson(record, self.bot)
            for student in students:
                if student is not None:
                    cur.execute("SELECT * FROM studentLessons WHERE studentId = ? AND classId = ?", (student.id, lesson.id))
                    if cur.fetchone() is None:
                        cur.execute("INSERT INTO studentLessons VALUES (?,?,?)", (student.id, lesson.id, ctx.guild.id))
            
            await ctx.send("All students have beeen added run the command again to add more!")
            con.commit()
        
        @cog_ext.cog_slash(name="createlesson", description="Creates a lesson", guild_ids=guild_ids, options = [create_option(name="name",description="The name of the Lesson (must be unique)", required=True, option_type=3),
                                                                                                                create_option(name="subject",description="The subject of the lesson", required=True, option_type=3), 
                                                                                                                create_option(name="time", description="The time of the event in the format DD/MM/YYYY HH:MM", required=True, option_type=3),
                                                                                                                create_option(name="duration", description="How many minutes the lesson goes on for", required=True, option_type=4),
                                                                                                                create_option(name="repeat_weekly", description="Sets whether the lesson repeats this time and day every week", required=True, option_type=5),
                                                                                                                create_option(name="description", description="Anything you want to say about the lesson", required=True, option_type=3)])   
        async def createLesson(self, ctx: discord_slash.SlashContext, name, subject, time, duration, repeat_weekly, description):
            
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


            payload =(self.generateId(), ctx.guild.id, name, time, subject, ctx.author.id, repeat_weekly, description, duration, None, None, None,)
            newLesson = self.Lesson(payload, self.bot) # Creating a lesoon object
            print(len(payload))
            cur.execute("INSERT INTO lessons VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", payload)
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
                    lesson = self.Lesson(lesson, self.bot)
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





        @tasks.loop(seconds=60)
        async def checkForLesson(self):
            
            now = datetime.utcnow()
            
            now = now + timedelta(minutes=1) + timedelta(hours=1)
            now = datetime(now.year, now.month, now.day, 22, 20, 0)
            frmt = "%Y-%m-%d %H:%M:00"
            print("checking..")
            cur.execute("SELECT * FROM lessons")
            nowstrf = now.strftime(frmt)
            cur.execute("SELECT * FROM lessons WHERE dateTime = ?",(nowstrf,))
            records = cur.fetchall()
            for record in records:

                lesson = self.Lesson(record, self.bot)
                print("starting")
                await lesson.start()
                
        @checkForLesson.before_loop
        async def before_check(self):

            await self.bot.wait_until_ready()
            now = datetime.utcnow()
            future = datetime(now.year, now.month, now.day, now.hour, now.minute+1, 0, 0)
            print("Sleeping for {0} seconds".format((future - now).seconds))
            await asyncio.sleep((future - now).seconds)


        async def formatMembers(self, members):
            if len(members) == 0:
                return "No students yet"
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
            
            return students

def setup(bot):
    bot.add_cog(Lessons(bot))
