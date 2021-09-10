import discord
from discord.ext import commands, tasks
import logging
import asyncio
import logging.handlers
import sqlite3
from discord_slash import SlashCommand, context, cog_ext
import discord_slash
from discord_slash.utils.manage_commands import create_option
logger = logging.getLogger("bot") # Gets the logger we defined in main.py

con = sqlite3.connect("resources/databases/schooldata.db")

cur = con.cursor()
#cur.execute("CREATE TABLE schoolGuilds (guildID integer,schoolName text,schoolAbreviation text,studentRoleId integer,teacherRoleId integer,managerRoleId integer)")
#cur.execute("INSERT INTO schoolGuilds VALUES (?,?,?,?,?,?)", ((836901717160886292, "Devenport High School For Boys"," DHSB", 878108466894479360, 878108465866899497, 878108465669758996)))
#con.commit()
 #(guildID integer,schoolName text,schoolAbrieviation text,studentRoleId integer,teacherRoleId integer,managerRoleId integer)
########### SETUP OPTIONS##############
schoolName =  create_option(
                    name="school_name",
                    description="This is the name of the school (you can change this later)",
                    option_type=3,
                    required=True
) 
schoolAbr =  create_option(
                    name="school_abreviation",
                    description="This is the shortened version of the school name this will be used in channels",
                    option_type=3, ## option type 3
                    required=True
) 
studentRole =  create_option(
                    name="student_role",
                    description="This will be the name of the role given to students!",
                    option_type=3, ## option type 8 means that the data will be taken as a ROLE object 
                    required=False
) 
teacherRole =  create_option(
                    name="teacher_role",
                    description="This is the name of the role for teachers",
                    option_type=3,
                    required=False,
)
managerRole = create_option(
                    name="manager_role",
                    description="This is a role for managers (you can add managers later, you automatically will get this role.",
                    option_type=3,
                    required=False,
) 
helpChannelNames = ["Ash", "Birch", "Cedar", "Dragon", "Elm", "Fir","Garjan", "Hazel", "Ivorypalm", "Juniper", "Kapok", "Locust", "Mombin","Nutmeg", "Oak", "Palm","Sapel", \
                    "Teak", "Upas", "Wingnut", "Yew", "Zelkova" ]           
guild_ids = [836901717160886292, 883409165391896626, 884796354390523974] # contains the guildId of the test OCR setver
class Setup(commands.Cog):
        def __init__(self, bot):
            self.bot = bot 
        
        @commands.Cog.listener()
        async def on_ready(self):
            logger.debug("Setup cog is ready!") # This message will be displayed when the cog is ready
        
        
        @cog_ext.cog_slash(name="deletehelpdata", description="If Help is has broken it can be reset here", guild_ids=guild_ids)
        async def resetHelp(self, ctx: discord_slash.SlashContext):
            cur.execute("SELECT channel_Id FROM help_channels WHERE guild_id = ?", (ctx.guild.id,))
            records = cur.fetchall()
            guild = ctx.guild
            for x in records:
                
                channel = guild.get_channel(x[0])
                if channel is not None:
                    await channel.delete()
                else:
                    continue
            cur.execute("SELECT category_id FROM subjects WHERE guildID = ?", (ctx.guild.id,))
            records = cur.fetchall()

            for x in records:
                catChannel = guild.get_channel(x[0])
                if catChannel is not None:
                    await catChannel.delete()
                else:
                    continue
            cur.execute("SELECT avaliableCategoryId, dormantCategoryId FROM schoolGuilds")
            record = cur.fetchone()
            try:
                guild.get_channel(record[0]).delete()
                guild.get_channel(record[1]).delete()
            except:
                pass
            cur.execute("DELETE FROM help_channels WHERE guild_id = ?", (ctx.guild.id,))
            cur.execute("DELETE FROM subjects WHERE guildID = ?", (ctx.guild.id,))
            con.commit()
            await ctx.send("All help data has been deleted do /setuphelp to set help up again")
        @cog_ext.cog_slash(name="setup", ### 
                            description ="Set up the server to be how the bot needs it",
                            options = [schoolName, schoolAbr, studentRole, teacherRole, managerRole], guild_ids=guild_ids)
        async def setUpServer(self, ctx: discord_slash.SlashContext, school_name: str, school_abreviation: str, student_role: str = None, teacher_role: str = None, manager_role: str = None): # ctx returns the context of the command. Etc what server it was executed in or who executed it
            await ctx.defer()
            cur.execute("SELECT * FROM schoolGuilds WHERE guildID=:guildId", {"guildId": ctx.guild.id} )
            record = cur.fetchone()
           
            if record is None or record == []:
                    cur.execute("SELECT * FROM schoolGuilds")
                    #print(cur.fetchall())
                    guild = ctx.guild # Just saves a bit of typing 
                    studentRoleName = "Student" if student_role is None else student_role # If the user didnt specify a name for the roles the role name will default to Student
                    teacherRoleName = "Teacher" if teacher_role is None else teacher_role
                    managerRoleName = "Manager" if manager_role is None else manager_role    
                    mRole= await guild.create_role(name= managerRoleName, hoist = True, mentionable=True) # manager Role hoist allows there role to be visible in the online list and mentionable allows them to be mentioned (@managers)
                    tRole= await guild.create_role(name= teacherRoleName, hoist = True, mentionable=True) # teacher Role                

                    
                    roleNames = [("Rookie", 0xffa200), ("Amateur", 0xffdd00), ("Experienced", 0x006eff), ("Expert", 0x00c3ff),  ("Master", 0x00ff1a), ("Epic", 0xc300ff), ("Legendary", 0x0dff00), ("Ultimate", 0xea00ff),("GOD", 0xffffff)]
                    for x in range(8, -2, -1):
                        
                        if x != -1:
                            name = roleNames[x][0] + " Helper"
                            role = await guild.create_role(name=name, hoist =True, mentionable=False, colour=roleNames[x][1])
                        cur.execute("INSERT INTO helpRoles VALUES (?, ?, ?)", (role.id, ctx.guild.id, (x+2)*10))
                

                

                    sRole = await guild.create_role(name= studentRoleName, hoist =True, mentionable=True) # Student Role                
                
                
                
                
                    

                    #positions = {
                    #    mRole: 5,
                   #     tRole: 4,
                   #     sRole: 3,
                    #}
                    #await guild.edit_role_positions(positions=positions)
            
                    await guild.me.add_roles(mRole)



                    overwrites = {sRole: discord.PermissionOverwrite(send_messages = False),
                                guild.default_role: discord.PermissionOverwrite(send_messages = False)
                            } # Only teachers and managers can make announcements

                    await guild.create_text_channel(name="Announcements")
                    generalChannels = await guild.create_category(name="General channels")
                    await guild.create_category(name="Private Voice channels")
                    await guild.create_category(name="Your Active lessons voice channels")

                    overwrites = {sRole: discord.PermissionOverwrite(read_messages = False)} # Students dont have the permission to read teacher channels
                    teachers = await guild.create_category(name="Teacher chat", overwrites=overwrites)
                    await asyncio.sleep(2)
                    await teachers.create_text_channel(name="teachers-chat")
                    await teachers.create_voice_channel(name="Teachers VC")
                    overwrites = {
                                tRole: discord.PermissionOverwrite(read_messages = False),
                                sRole: discord.PermissionOverwrite(read_messages = False)
                                } # Teachers dont have permission to read manager channels and neither do students

                    managers = await guild.create_category(name="Manager chats", overwrites=overwrites)
                    await managers.create_text_channel(name="managers-chat")
                    await managers.create_voice_channel(name="Managers VC")
                    

                    
                    try:
                        await generalChannels.create_text_channel(name=f"{school_abreviation}-general") # creating channels in the "General channels category"
                        await generalChannels.create_text_channel(name=f"{school_abreviation}-offtopic")
                        await generalChannels.create_text_channel(name=f"{school_abreviation}-resources") 
                    except Exception as e:
                        print(f"Error when creating channels\n{e}")


                    
                    # (guildID integer,schoolName text,schoolAbrieviation text,studentRoleId integer,teacherRoleId integer,managerRoleId integer)
                    cur.execute("INSERT INTO schoolGuilds VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (int(ctx.guild.id), school_name, school_abreviation,int(sRole.id),  int(tRole.id), int(mRole.id), 0,  0, 0, 0))
                    embed = discord.Embed(title= "Server Set up!",)
                    embed.add_field(name="What to do now?", value="Now that all the neccesary channels have been created as long as you don't delete any or add any channels to the help categories or the active lessons catagory, feel free to customize the server how you want! If you want custom names for \
                        categories and channels feel free to do so! Add descriptions to channels to tell your students what to use the channel for, add a server picture! We recommend you delete the default channels that discord may have created because they are redundant. Change the colours of the roles or even add new roles!"
                        )
                    embed.add_field(name="Make sure you dont!",value="- Delete the Student, Teacher or Manager Roles\n- Delete any of the help channels or any active lessons \n- Remove administrator from me", inline=False)
                    con.commit()

                    
                    await ctx.send(embed=embed)
            else:

                await ctx.send("You've already set up your server! if you want to reset it do /resetserver")
        @cog_ext.cog_slash(name="setuphelp", guild_ids=guild_ids, description="To set up a help system in the server",options=[create_option(name="subject1", description="A subject your school offers!", option_type=3,required=True),
                                                                                                        create_option(name="subject2", description="A subject your school offers!", option_type=3,required=True),
                                                                                                        create_option(name="subject3", description="A subject your school offers!", option_type=3,required=True),
                                                                                                        create_option(name="subject4", description="A subject your school offers!", option_type=3,required=False),
                                                                                                        create_option(name="subject5", description="A subject your school offers!", option_type=3,required=False),
                                                                                                        create_option(name="subject6", description="A subject your school offers!", option_type=3,required=False),
                                                                                                        create_option(name="subject7", description="A subject your school offers!", option_type=3,required=False),
                                                                                                        create_option(name="subject8", description="A subject your school offers!", option_type=3,required=False),
                                                                                                        ])
        async def setupHelp(self, ctx: discord_slash.SlashContext, subject1, subject2, subject3, subject4=None, subject5=None, subject6=None, subject7=None, subject8=None):
                guild = ctx.guild
                await ctx.defer()
                cur.execute("SELECT * FROM schoolGuilds WHERE guildID=:guildId", {"guildId": ctx.guild.id})
                if cur.fetchone() is not None:
                    cur.execute("SELECT * FROM help_channels WHERE guild_id=:guildId", {"guildId": ctx.guild.id})
                    
                    if cur.fetchone() is None:
                            cur.execute("SELECT studentRoleId, teacherRoleId FROM schoolGuilds WHERE guildID=:guildId", {"guildId": ctx.guild.id})
                            record = cur.fetchone()
                            cdRole = await guild.create_role(name="Help cooldown", mentionable=False)

                            avaliable = await guild.create_category(name="✅ | Avaliable help channels!" )
                            student = guild.get_role(int(record[0]))
                            teacher = guild.get_role(int(record[1]))
                            # Help cooldown role (people who have this role will not be able to claim a help channel)
                            overwrites = {
                                student: discord.PermissionOverwrite(read_messages=False),
                                cdRole: discord.PermissionOverwrite(send_messages=False, read_messages=True),
                                
                            }
                            cdChannel = await avaliable.create_text_channel(name="🔴COOLDOWN🔴", overwrites=overwrites)
                            embed = discord.Embed(title="You are currently on cooldown!!", description="You are currently on cooldown! This means you can't claim another help channel. \
                                 If after 30 minutes no one has come to help you, feel free to open another help channel!", colour=0xFF0000)
                            await cdChannel.send(embed=embed)

                            positions = {

                                student:1,
                                cdRole: 2

                            }
                            await guild.edit_role_positions(positions=positions)
                            subjects = [subject1, subject2, subject3, subject4, subject5, subject6, subject7] # list of the subjects
                            overwrites = {student: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                                        cdRole: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
                            channel = await guild.create_category(name= f"General help questions", overwrites=overwrites)
                            
                            cur.execute(f"INSERT INTO subjects VALUES (?, ?, ?)", (guild.id, "general", channel.id))
                            for subject in subjects:
                                if subject is None: # If one of the subjects in the list is None it means all the subjects after it are also None so there we break out of the loop
                                    continue  #   
                                else:
                                    channel = await guild.create_category(name=f"🙋 |We Need Help with {subject}", overwrites=overwrites) # EG Help with chemistry
                                    await asyncio.sleep(0.2)
                                    cur.execute(f"INSERT INTO subjects VALUES (?, ?, ?)", (guild.id, subject, channel.id)) # Storing the subject in the database
                                
                                con.commit()
                                    
                      
                            overwrites = {
                            guild.default_role: discord.PermissionOverwrite(send_messages = False),
                            student: discord.PermissionOverwrite(send_messages=False, ),
                            teacher: discord.PermissionOverwrite(send_messages=False, read_messages=True)
                            }
                            dormant = await guild.create_category(name="💤 | Dormant help channels",overwrites=overwrites) # This will create the channel and set the  object to dormant
                            cur.execute("UPDATE schoolGuilds  SET avaliableCategoryId= :av, dormantCategoryId= :do, cooldownRoleId = :cr, cooldownChannelId = :cc WHERE guildID = :gu", {"av": avaliable.id, "do": dormant.id, "gu": guild.id, "cr": cdRole.id, "cc": cdChannel.id })

                            for word in helpChannelNames: # creates 26 channels with different tree names
                                counter = 0
                                name ="help-" + word.lower() # etc help-oak
                                channel = await dormant.create_text_channel(name=name, position=counter, topic=f"The {word} help channel", overwrites=overwrites)
                                
                                cur.execute(f"INSERT INTO help_channels VALUES ({channel.id}, {ctx.guild.id})") # Storing all help channels into the data base
                                counter +=1
                                avaliableEmbed = discord.Embed(title="This help channel is avaliable!", description="To claim this help channel type (SUBJECT) then your question after. \
                                                            For example: \n\n*(COMPUTER SCIENCE) Are dictionaries in python ordered or unordered?*\n\n Alternatively, if your question isnt tied to a subject just add (GENERAL)  \
                                                                before your question for example:\n\n*(GENERAL) Where is the assembly today taking place?*\n\n hopefully someone can help!", colour=0x3ee800)
                                dormantEmbed = discord.Embed(title="This help channel is dormant.", description="If you need help look at the avaliable channels category for more do the \
                                    command /howtogethelp!", colour = 0xff2b2b)
                                await asyncio.sleep(0.2)
                            con.commit()

                            
                            overwrites = {
                            guild.default_role: discord.PermissionOverwrite(send_messages = False),
                            student: discord.PermissionOverwrite(send_messages=True),
                            cdRole: discord.PermissionOverwrite(read_messages=False, send_messages=False)
                            }                                    
                            for x in range(3):
                                channel=dormant.channels[x]
                                await channel.edit(category=avaliable, overwrites=overwrites)
                                await channel.send(embed=avaliableEmbed)
                                await asyncio.sleep(0.2)
                            for channel in dormant.channels:
                                await channel.send(embed=dormantEmbed)
                                await asyncio.sleep(0.2)
                            await ctx.send("Help has been set up! Make sure you don't delete any of the help channels or subjects")
                    else:
                        await ctx.send("You've already set up help! If you want to delete help data and channels because there is a problem do /deletehelpdata")
                else:
                    await ctx.send("You haven't set up your server! use /setup first then you can set up help!")
                        


def setup(bot):
    bot.add_cog(Setup(bot))




            