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
guild_ids = [836901717160886292, 883409165391896626,884796354390523974,899703139840708668]
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
                else: # You never know.... 
                    print(cur.fetchone())
                    continue
        class Lesson():

            def __init__(self, payload, bot): # pass the bot object to get the guild and the teacher objects
                self.bot = bot
                self.id = payload[0]
                self.guild = bot.get_guild(payload[1])# guild object
                self.name = payload[2]
                self.dateTime = payload[3]
                self.subject = payload[4]
                self.teacher = self.guild.get_member(payload[5]) # getting teacher object
                self.repeatWeekly = payload[6]
                self.description = payload[7]
                self.lessonDuration = payload[8]
                self.vc = payload[9] # voice chat
                self.tc = payload[10] # text chat
                self.embedMessage = payload[11]    
    
            def fetch_students(self):
                cur.execute("SELECT studentId FROM studentLessons WHERE classId = ?", (self.id,))
                records = cur.fetchall()
                students = [self.guild.get_member(x[0]) for x in records] # returns a list of member object
                return students
            
            async def start(self):

                students = self.fetch_students() 

                cur.execute("SELECT activeLessonsCategoryId, waitingRoomId FROM schoolGuilds WHERE guildID = ?", (self.guild.id,))
                records = cur.fetchone() 
                activeLessonCat = self.guild.get_channel(records[0]) ##geting channel objects by ID
                waitingRoom = self.guild.get_channel(records[1])

                
                role = await self.guild.create_role(name=self.name) # lesson specific role
                overwrites = {
                    self.guild.default_role: discord.PermissionOverwrite(read_messages=False), # Normal people should not be able to see this channel
                    role: discord.PermissionOverwrite(read_messages=True) # People with the lesson role can see and join the lesson
                }
                self.vc = await activeLessonCat.create_voice_channel(name=self.name, overwrites=overwrites) 
                
                self.tc = await activeLessonCat.create_text_channel(name=self.name+"-text", overwrites=overwrites)
                embed = discord.Embed(title=f"Your {self.subject} lesson is starting now!", description=f"{self.name} is starting now!" )
                embed.add_field(name="Voice channel", value=f"Join the voice channel by clicking this link > {self.vc.mention}")
                embed.add_field(name="Text channel", value=f"View the text channel by clicking this > {self.tc.mention}\n\n**TIP:** If you join {waitingRoom.mention} then you will automatically get moved into your lesson when it starts!")
                infoEmbed = discord.Embed(title="Lesson Info", description=f"This lesson is being taught by {self.teacher.mention}")
                notJoinedStudents = students
                joinedStudents = []


                for student in students: # adding the role to each student in the class and sending them a message notifying their lesson is starting now, and info about the lesson
                    await student.add_roles(role) 
                    await student.create_dm()
                    await student.dm_channel.send(embed=embed)

                studentsStr = ""
                for student in notJoinedStudents:
                    studentsStr += f"{student.mention}\n"
                joinedStudentsStr = ""
                for student in joinedStudents:
                    joinedStudentsStr +=f"{student.mention}\n" # formatting students for the embed
                
                joinedStudentsStr = "No students have joined yet" if len(joinedStudents) == 0 else joinedStudentsStr 
                infoEmbed.add_field(name="Students who have joined", value=joinedStudentsStr,inline=False)
                infoEmbed.add_field(name="Students who haven't joined",value=studentsStr, inline=False)             

                message = await self.tc.send(embed=infoEmbed)
                                
                cur.execute("UPDATE lessons SET VC = ?, TC = ?, embed=? WHERE classId = ?", (self.vc.id,self.tc.id,message.id, self.id)) # Fixing the database showing all these as NONE
                con.commit()
                if self.teacher in waitingRoom.members: # If the teacher is in the waiting room we move them to the lesson voice chat
                    await self.teacher.add_roles(role)
                    await self.teacher.move_to(self.vc) 
                    await self.teacher.create_dm()
                    await self.teacher.dm_channel.send(embed=embed)
                for member in waitingRoom.members: # iterating through the members in the waiting room
                    if member in notJoinedStudents: # if member hasnt joined
                        await member.move_to(self.vc) # move them to the leson vc
                        notJoinedStudents.remove(member) # transfer them to the joined list
                        joinedStudents.append(member)

                await asyncio.sleep((self.lessonDuration+5)*60) # we give them an extra 5 minutes before the lesson chats are deleted
                await self.vc.delete()
                await self.tc.delete()
                if not self.repeatWeekly(): # if this is lesson is not repeating we just
                    cur.execute("DELETE FROM lessons WHERE classId = ?", (self.id,))
                    for student in students:
                        await student.remove_roles(role) 
                else:
                    time = datetime.fromisoformat(self.dateTime)
                    self.dateTime = time + timedelta(days=7)
                    cur.execute("UPDATE lessons SET VC = null, TC = null, embed=null, dateTime = ? WHERE classId = ?", (time.isoformat(), self.id))
                await role.delete()
                con.commit()
                
        @commands.Cog.listener()
        async def on_voice_state_update(self, member, before, after):
            if not (after.deaf or after.mute or after.self_deaf or after.self_mute or after.self_stream or after.self_video) : # Making sure that the voice state is that someone joined or left
                cur.execute("SELECT activeLessonsCategoryId FROM schoolGuilds WHERE guildID = ?", (member.guild.id,)) # getting the active lessons category
                activeLessonsCat = cur.fetchone() 
                activeLessonsCat = member.guild.get_channel(activeLessonsCat[0])
                if after.channel in activeLessonsCat.channels or before.channel in activeLessonsCat.channels: # If the voice channel is an active lesson voice chat
                    if after.channel in activeLessonsCat.channels: # If person joined
                        lessonChannel = after.channel
                    elif before.channel in activeLessonsCat.channels: # If person left
                        lessonChannel = before.channel

                    cur.execute("SELECT * FROM lessons WHERE VC = ?", (lessonChannel.id,))
                    payload = cur.fetchone()
                    lesson = self.Lesson(payload, self.bot) ## getting all the lesson info then fetching all the objects
                    channel = member.guild.get_channel(lesson.tc)
                    message =await channel.fetch_message(lesson.embedMessage)
                    embed = message.embeds[0]
                    notJoinedStudents = lesson.fetch_students()
                    voice = member.guild.get_channel(lesson.vc)
                    joinedStudents = voice.members
                    if lesson.teacher in joinedStudents: # making sure to exclude the teacher from joinedStudents if he/she is in it
                        joinedStudents.remove(lesson.teacher)

                    for student in notJoinedStudents:
                        if student in joinedStudents:
                            notJoinedStudents.remove(student) # removing joined students from not joined students so that the only people left in notJoinedStudents are people who havent joined
                    
                    students = ""
                    for student in notJoinedStudents:
                        students += f"{student.mention}\n"
                    joinedStudentsStr = ""
                    for student in joinedStudents:
                        joinedStudentsStr +=f"{student.mention}\n"
                    if joinedStudentsStr == "":
                        joinedStudentsStr = "No students have joined yet"
                    if students == "":
                        students = "All students have joined!"
                    ## formating
                    embed.set_field_at(0, name="Students Who have joined", value=joinedStudentsStr)
                    embed.set_field_at(1, name="Students Who haven't joined", value= students)
                    await message.edit(embed=embed) # edit the embed to reflext the new data

                    if before.channel == lessonChannel: # Notifying if students have left the call
                        await lesson.teacher.create_dm()
                        await lesson.teacher.dm_channel.send(f"{member.name} just left the call!")
                        await channel.send(f"{member.name} just left the call!")
                    if lessonChannel == after.channel():
                        time = datetime.fromisoformat(self.dateTime)
                        now = datetime.utcnow()
                        difference = (now - time).seconds
                        difference = round(difference/60) # calculating minutes late
                        await lesson.teacher.dm_channel.send(f"{member.name} is {difference} minutes late!") # sending the teacher the dm
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
            lesson = self.Lesson(cur.fetchone(), self.bot) # getting the lesson object
            time = datetime.fromisoformat(lesson.dateTime) # time of lesson

            format = "Repeats every %A @ %I:%M %p"  if lesson.repeatWeekly else "Lesson is at %A %d/%m/%y"
            time = time.strftime(format) 

            info =f"**{lesson.subject}**\nDescription: {lesson.description}\n\nTime: {time}"
            embed = discord.Embed(title=lesson.name, description=info)
            teacher = lesson.teacher
            embed.add_field(name="Teacher", value=f"{teacher.mention}")
            members = lesson.fetch_students()
            members = [[member.name, member] for member in members] # returns a 2D array of [member.name, member] for each student
            students = await self.formatMembers(members) # we format this 
            

            embed.add_field(name="Students", value=students, inline=False)# adding student embed

            await ctx.send(embed=embed) #Sending embed
             
        @cog_ext.cog_slash(name="listlessons", description="Lists your lessons!", guild_ids=guild_ids, options = [create_option(name="page", description="The page of lessons you want to see",required=False, option_type=4)])
        async def listLessonsCommand(self, ctx, page=None):
            page = 1 if page is None else page
            cur.execute("SELECT teacherRoleId, studentRoleId FROM schoolGuilds WHERE guildID = ? ", (ctx.guild.id,))
            record = cur.fetchone() # fetches the one (and only) record
            teacher = ctx.guild.get_role(record[0])  # Gets the role objects
            student = ctx.guild.get_role(record[1])
            if teacher in ctx.author.roles: # If the member is a teacher 
                cur.execute("SELECT * FROM lessons WHERE teacherId = ?", (ctx.author.id,))
                records = cur.fetchall() # just fetch all the lessons where the person executing the command is the teacher
            elif student in ctx.author.roles:# if the member is a student
                cur.execute("SELECT classId FROM studentLessons WHERE guildId = ? AND studentId = ?",(ctx.guild.id, ctx.author.id))
                # The reason we add where guildId = ctx.guild.id is because if the bot is running on multiple servers we need to specify which server we are working in
                records = cur.fetchall()
                ids = [x[0] for x in records] # We get all lessons for the student in this particulart server
                records = []
                for id in ids: 
                    cur.execute("SELECT * FROM lessons WHERE classId = ?", (id,)) # getting the rest of the lesson info
                    records.append(cur.fetchone()) #We append a tuple of info (these will be converted to lesson objects in the listLessons command)
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
                    cur.execute("SELECT * FROM studentLessons WHERE studentId = ? AND classId = ?", (student.id, lesson.id)) #This checks if the student is already in the lesson
                    if cur.fetchone() is None: # if cur.fetchone() is none then that means that the student hasnt already got the 
                        cur.execute("INSERT INTO studentLessons VALUES (?,?,?)", (student.id, lesson.id, ctx.guild.id))
                else:
                    break
            await ctx.send("All students have beeen added run the command again to add more!")
            con.commit()
        
        @cog_ext.cog_slash(name="createlesson", description="Creates a lesson", guild_ids=guild_ids, options = [create_option(name="name",description="The name of the Lesson (must be unique)", required=True, option_type=3),
                                                                                                                create_option(name="subject",description="The subject of the lesson", required=True, option_type=3), 
                                                                                                                create_option(name="time", description="The time of the event in the format DD/MM/YYYY HH:MM", required=True, option_type=3),
                                                                                                                create_option(name="duration", description="How many minutes the lesson goes on for", required=True, option_type=4),
                                                                                                                create_option(name="repeat_weekly", description="Sets whether the lesson repeats this time and day every week", required=True, option_type=5),
                                                                                                                create_option(name="description", description="Anything you want to say about the lesson", required=True, option_type=3)])   
        async def createLesson(self, ctx: discord_slash.SlashContext, name, subject, time, duration, repeat_weekly, description):
            
            dateMatch = re.match("(\d{2})\/(\d{2})\/(\d{4}) (\d{2}):(\d{2})", time) # matching to the syntax XX/XX/XXXX XX:XX
            if dateMatch:
                time = "" + dateMatch.group(3) + "-"+dateMatch.group(2) + "-" + dateMatch.group(1) + " " + dateMatch.group(4) + ":" + dateMatch.group(5) #putting the date in the right format

            else:
                await ctx.send("Incorrect syntax for time")
                return

            try:
                time = datetime.fromisoformat(time) # gets datetime object from ISO format string

            except Exception as e:
                
                await ctx.send("There is something wrong with the time you entered. Are you sure it's right?") # Error is most likely because of an invalid time
                return
            cur.execute("SELECT * FROM lessons WHERE teacherId = ? AND LOWER(name) = ?", (ctx.author.id, name.lower()))
            if cur.fetchone() is not None:
                await ctx.send(f"You already have a class named {name}!") # All names must be different
                return
            cur.execute("SELECT teacherRoleId FROM schoolGuilds WHERE guildID = ?", (ctx.guild.id, )) #Get the teacherRoleId
    
            roleId = cur.fetchone() # this will return a tuple with one value 
            roleId = roleId[0] # take the one value in the tuple
            role = ctx.guild.get_role(roleId) # get the role object from ID
            
            if role not in ctx.author.roles: # If the author doesnt have a teacher role he/she is not a teacher
                await ctx.send("Only teachers can create lessons! If you feel this is in error do /info to see the bot roles. Roles needed for the bot to work may have been deleted and/or replaced.")
                return  


            payload =(self.generateId(), ctx.guild.id, name, time, subject, ctx.author.id, repeat_weekly, description, duration, None, None, None,) # There is no Textchannel, Voicechat or embed yet.
            newLesson = self.Lesson(payload, self.bot) # Creating a lesoon object
            cur.execute("INSERT INTO lessons VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", payload)
            con.commit() # commits changes
            await ctx.send(f"Created new {newLesson.subject} lesson at {newLesson.dateTime}!")

        async def listLessons(self, lessons, page):
            total = len(lessons)
            lastPage = total % 8 # divide by how many terms we want in our embed and throw away the remainder
            if lastPage == 0:
                lastPage = int(total / 8) # If its divisible by 8 then the last page will be full 
            else:
                lastPage = int((total // 8) + 1) # if not we would need an extra page for the remaining lessons  
        
            if page >= 1 and page <= lastPage: #If the page exists
                embed = discord.Embed( # Base embed.
                    title="Your lessons!",
                    description="These are all of your lessons:",
                )
                text = "page {0}/{1}".format(page, lastPage)
                embed.set_footer(text=text) # this will show the user what page they are on
                counter = 1
                for lesson in lessons:
                    lesson = self.Lesson(lesson, self.bot)
                    if counter > (8 * (page - 1)) and counter < ((page * 8)+1):
                        time = datetime.fromisoformat(lesson.dateTime)
                        if lesson.repeatWeekly: 
                            format = "%A @ %I:%M %p" 
                            time = time.strftime(format)
                            embed.add_field(name=lesson.name, value=f"Subject: {lesson.subject}\nRepeats every week {time}", inline=False) # if it repeats weekly show the day and time it repeats
                        else:
                            format = "%A %d/%m/%y"
                            time = time.strftime(format)
                            embed.add_field(name=lesson.name, value=f"Subject: {lesson.subject}\nLesson is at {time}", inline=False) # If it isnt                    

            
                    counter += 1
                
                return embed
            else:
                return None


        @tasks.loop(seconds=60)
        async def checkForLesson(self):
            
            now = datetime.utcnow() # now
            
            now = now + timedelta(minutes=1) + timedelta(hours=1) # adding an hour because in the UK we are +01:00
            frmt = "%Y-%m-%d %H:%M:00"

            cur.execute("SELECT * FROM lessons")
            nowstrf = now.strftime(frmt)
            cur.execute("SELECT * FROM lessons WHERE dateTime = ?",(nowstrf,)) # selecting all lessons that start now
            records = cur.fetchall()
            for record in records:

                lesson = self.Lesson(record, self.bot)

                await lesson.start() # starting all these lessons
                
        @checkForLesson.before_loop
        async def before_check(self):
            await self.bot.wait_until_ready() # Make sure the bot is ready before doing anything
            now = datetime.utcnow()
            future = datetime(now.year, now.month, now.day, now.hour, now.minute, 0, 0) + timedelta(minutes=1) # waiting until the next minute
            print("Sleeping for {0} seconds".format((future - now).seconds))
            await asyncio.sleep((future - now).seconds) # Sleep for however many seconds it takes to get to the next minute


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
