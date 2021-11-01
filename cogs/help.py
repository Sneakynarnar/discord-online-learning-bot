import discord
from discord import File
from discord.ext import commands, tasks
import sqlite3
import asyncio
import logging
import logging.handlers
import discord_slash
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from discord_slash import SlashCommand, cog_ext
import regex as re
import io
import json
import math
from datetime import timedelta
from discord_slash.utils.manage_commands import create_option
from datetime import datetime
cooldownTime = 30
logger = logging.getLogger("bot")
con = sqlite3.connect("resources/databases/schooldata.db")
cur = con.cursor()
BASE_REWARD = 250
guild_ids = [836901717160886292, 883409165391896626,884796354390523974,899703139840708668]
class Help(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
            self.questions = {}

            #with open("resources/databases/questions.json", "r") as F:
                #self.questions = json.load(F)
            
            self.channelExpiration.start()
        @cog_ext.cog_slash(name="exp", guild_ids=guild_ids, description="Describes how to get help", options = [create_option(name="member", description="The person you want to give exp",required=True, option_type=6),
                                                                                                                    create_option(name="amount", description="The amount of exp",required=True, option_type=4)])
        async def exp(self, ctx: discord_slash.SlashContext,member, amount):
            if amount > 0:
                await self.addExp(member, amount, ctx.guild, False)
                await ctx.send(f"{amount} exp added!")
            else:
                await ctx.send("You cant add negative or 0 exp!!")
        @cog_ext.cog_slash(name="howtogethelp", guild_ids=guild_ids, description="Describes how to get help")
        async def howToGetHelp(self, ctx: discord_slash.SlashContext):
            cur.execute("SELECT avaliableCategoryId FROM schoolGuilds WHERE guildID = ?", (ctx.guild.id,))
            id = cur.fetchone()
            id = id[0]
            channel = ctx.guild.get_channel(int(id))
            file = discord.File("resources/images/htgh.gif", "htgh.gif")
            embed = discord.Embed(title="Understanding the help channels", description="The help system tries to make it easier for students to get help from other students or teachers. To get help using the help channel system you must:\n **1.** Find an avaliable help channel, \
                                                                                    avaliable help channels are in the **\"{0}\"** category. You will know when its avaliable when the message on the channel  \
                                                                                        says it is.\n**2.** When found you can claim the help channel!, to do this you must specify what subject you need help with by typing (SUBJECT) before then ask your question!. Make sure the subject \
                                                                                            you type is a subject your school offers by doing /subjects.\n**3.** Play the waiting game and wait for another student or a teacher to help! Students are rewarded with cosmetic roles for helping in \
                                                                                                 these channels. Maybe you can help in a subject that your confident in by checking if the category for that subject \
                                                                                                    The more people you help the more cosmetic roles you get and helping people is just nice for your school community\nThere is an example below\n\n**NOTE:** Help channels are automatically \
                                                                                                        closed after 30 minutes of inactivity. You can close it whenever you want with /close though.".format(channel.name))
            embed.set_image(url="attachment://htgh.gif")                                                                         
            
            await ctx.send(embed=embed, file=file)
            
        @cog_ext.cog_slash(name="selfishclose",guild_ids=guild_ids, description="Closes the current help channel without rewarding anyone :(")
        async def selfishClose(self, ctx: discord_slash.SlashContext):
            cur.execute("SELECT guild_id FROM help_channels WHERE channel_id = ?", (ctx.channel.id,))
            if cur.fetchone() is not None:
                
                message = await ctx.channel.pins()
                message = message[0]
                if message.author == ctx.author:

                    await message.unpin()
                    await ctx.send("Closing help channel.")
                    await self.markAsDormant(ctx.channel)
                else:
                    await ctx.send("You can't close someone elses help channel!")
            else:
                await ctx.send("This isn't a help channel")
        @cog_ext.cog_slash(name="close",guild_ids=guild_ids, description="Closes the current help channel",options=[ 
                                                                                create_option(name="helper",description="Specify the person who helped you",required=True,option_type=6),
                                                                                create_option(name="rating",description="How much did this person help you? 1-10",required=False,option_type=4)])
        async def close(self, ctx: discord_slash.SlashContext, helper, rating=None):
            global BASE_REWARD
            rating = 5 if rating is None else rating # rating defaults to 5 if user doesnt specify a rating
            if rating <1 or rating >10:
                await ctx.send("That's not a rating between 1 and 10!")  # Ratings have to be between 1-19
                return
            
            cur.execute(f"SELECT * FROM helpLevels WHERE memberId = {helper.id} AND guildId = {ctx.guild.id}")
            if cur.fetchone() is None:
                cur.execute("INSERT INTO helpLevels VALUES (?,?,?,?,?)", (helper.id, ctx.guild.id, 0,0,1)) # if user has never gained exp before a new record is created for them
                record = (helper.id, ctx.guild.id, 0,0,0) 
            else:
                record = cur.fetchone() 
            cur.execute("SELECT guild_id FROM help_channels WHERE channel_id = ?", (ctx.channel.id,))
            if cur.fetchone() is not None:
                helpers = self.questions[str(ctx.channel.id)]["helpers"] # Checks if this person even sent a message in the help_channel
                if str(helper.id) not in helpers.keys():
                    await ctx.send("This person did not help you!") 
                    return       
                message = await ctx.channel.pins() 
                message = message[0] # There is should only be 1 pinned message, the question the user asked
                if message.author == ctx.author:
                    await message.unpin() 
                    await ctx.send("Closing help channel.")
                    rating /= 10
                    rating+=0.3
                    multiplier =1+rating if rating >0.5 else 1-rating
                    amount = BASE_REWARD*multiplier if rating != 0.5 else BASE_REWARD # Users should earn a minimum of BASE_REWARD. Exp given increases based on the rating
                    await self.addExp(helper, amount, ctx.guild) # Adds Exp
                    await self.markAsDormant(ctx.channel)
                else:
                    await ctx.send("You can't close someone elses help channel!")
            else:
                await ctx.send("This is not a help channel!")
        @cog_ext.cog_slash(name="rank",guild_ids=guild_ids, description="Specifies the rank of you or another member", options=[create_option(name="member",description="You can specify a member you want to see the rank of",required=False,option_type=6)])
        async def rank(self, ctx: discord_slash.SlashContext, member=None):
            if member is None:
                member = ctx.author

            cur.execute(f"SELECT * FROM helpLevels WHERE memberId = {member.id} AND guildId = {ctx.guild.id}")
            record = cur.fetchone()
            if record is None:
                cur.execute("INSERT INTO helpLevels VALUES(?,?,?,?,?)", (member.id, ctx.guild.id, 0,0,1))
                record = (member.id, ctx.guild.id, 0,0,1)

                
            buffer = await self.getRankImage(member, record[2], record[4], record[3], ctx.guild)
            await ctx.send(file=File(buffer, "rank.png"))

        @commands.Cog.listener()
        async def on_ready(self):
            logger.debug("Help cog is ready!")

        @commands.Cog.listener()  
        async def on_message(self, msg):
            now = datetime.utcnow()
            cur.execute("SELECT guild_id FROM help_channels WHERE channel_id = ?", (msg.channel.id,))
            guildId= cur.fetchone()
            if guildId is None:
                return
            else:
                guildId = guildId[0]
                guild = self.bot.get_guild(guildId)
                channel = msg.channel
                cur.execute("SELECT dormantCategoryId, avaliableCategoryId, coolDownRoleId FROM schoolGuilds WHERE guildID = ?", (guild.id,))
                record = cur.fetchone()
                avaliable = guild.get_channel(record[1]) ## getting channel objects
                dormant = guild.get_channel(record[0])
                cdRole = guild.get_role(record[2]) # cooldown roles
                cur.execute("SELECT category_id FROM subjects WHERE guildID = ? ", (guild.id,))
                channels = cur.fetchall()
                occupiedChannels = [x[0] for x in channels] # occupied subject category
                if msg.channel.category == avaliable: ## If its in the avaliable category, then its an avaliable help channel
                    logger.debug("Recognised avaliable channel")
                    msgList = msg.content.split()
                    try:
                        prefix = msgList[0]  # first word in the list
                    except:
                        return
                    subMatch = re.match("\((\D+)\)", prefix)  # Checking if the first word of the sentence is (WORD) so the person has the right syntax
                    if subMatch:
                        sub = subMatch.group(1)
                        cur.execute("SELECT subject, category_id FROM subjects WHERE guildID= ?", (msg.guild.id,))
                        subjects = cur.fetchall() ## get subject and categoryId
                        subject = None # initialise subject as None
                        for x in range(len(subjects)):
                            if subjects[x][0].lower() == sub.lower():
                                subject = subjects[x]
                            else:
                                continue
                        if subject is not None:
                            await msg.pin() ##pinning a message is like "bookmarking" a message a list of pinned messages can be seen in the channel
                          
                            subcat = guild.get_channel(subject[1])
                            overwrites = {cdRole: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
                            await msg.channel.edit(category=subcat, overwrites=overwrites) #Moves the channel to the subject occupied channel
                            await msg.author.create_dm() 
                            embed = discord.Embed(title="Help channel claimed!", description = f"You claimed the help channel {msg.channel.mention} for the subject {sub.lower()}")
                            embed.add_field(name="Your question", value=msg.content, inline=False)
                            link = "https://www.discord.com/channels/" + str(guild.id) +"/"+ str(channel.id) +"/" + str(msg.id)
                            embed.add_field(name="Link to message", value =f"[Click here to jump to your question]({link})")
                            await msg.author.dm_channel.send(embed=embed) # Sends the embed 
                            self.questions[str(msg.channel.id)] = {}
                            self.questions[str(msg.channel.id)]["owner"] = msg.author.id
                            self.questions[str(msg.channel.id)]["lastMessage"] = [now.year, now.month, now.day, now.hour, now.minute]
                            self.questions[str(msg.channel.id)]["messageId"] = msg.id
                            self.questions[str(msg.channel.id)]["helpers"] = {}
                            with open("resources/databases/questions.json", "w") as F: # Saves in a file just in case the bot goes down while their are open help_channels
                                json.dump(self.questions, F)
                            newAvaliableChannel = dormant.channels[0] #Selects the next dormant channel that replaces this avaliable channel once its claimed
                            cur.execute("SELECT studentRoleId FROM schoolGuilds WHERE guildID = ?", (msg.guild.id,)) # Gets the student roleId
                            role =cur.fetchone()
                            sRole = msg.guild.get_role(role[0]) # fetches student role object
                            overwrites = { # Making it so people on cooldown cant see avaliable channels.
                            guild.default_role: discord.PermissionOverwrite(send_messages = False),
                            sRole: discord.PermissionOverwrite(send_messages=True),
                            cdRole: discord.PermissionOverwrite(read_messages=False) 
                            }        
                            avaliableEmbed = discord.Embed(title="This help channel is avaliable!", description="To claim this help channel type (SUBJECT) then your question after. \
                                                            For example: \n\n*(COMPUTER SCIENCE) Are dictionaries in python ordered or unordered?*\n\n Alternatively, if your question isnt tied to a subject just add (GENERAL)  \
                                                                before your question for example:\n\n*(GENERAL) Where is the assembly today taking place?*\n\n hopefully someone can help!", colour=0x3ee800)
                            await newAvaliableChannel.edit(overwrites=overwrites) # New perms
                            await newAvaliableChannel.edit(category=avaliable) # changing the subjects to avaliable
                            await newAvaliableChannel.send(embed=avaliableEmbed)
                            await self.cooldown(msg.author, cdRole) # Puts the person who just claimed the channel (who is the author of the message) on cooldown
                        else:
                            await msg.author.create_dm()
                            await msg.author.dm_channel.send("That is not a subject the school has registered! If you believe this is in error tell managers to add this subject. To see a list of subjects in your school do /subjects")
                            await msg.delete()
                    else:
                        await msg.delete()
                        await msg.author.create_dm()
                        await msg.author.dm_channel.send("Make sure you put the subject name before your question! For example:\n\n (MATHS) How can I use the binomial infinite series to estimate pi? \n\n")
                elif msg.channel.category.id in occupiedChannels: # Sent a message in a channel thats already occupied
                    self.questions[str(msg.channel.id)]["lastMessage"] = [now.year, now.month, now.day, now.hour, now.minute] # Makes a record of the time the last message sent
                    if self.questions[str(msg.channel.id)]["owner"] == msg.author.id:
                        return
                    
                    if str(msg.author.id) not in self.questions[str(msg.channel.id)]["helpers"].keys(): # Adds the helper to the helpers list if they arent there already 
                        self.questions[str(msg.channel.id)]["helpers"][str(msg.author.id)] = 1
                    else:
                        self.questions[str(msg.channel.id)]["helpers"][str(msg.author.id)] +=1
                    with open("resources/databases/questions.json", "w") as F: # saving to file
                        json.dump(self.questions, F)  
                else:
                    pass
                    
                
                    
                    
                


        @tasks.loop(seconds = 60)
        async def channelExpiration(self):
            deleteList = [] 
            global BASE_REWARD
            for k, v in self.questions.items(): # iterating though all occupied help channels
                lastMessageDate = datetime(v["lastMessage"][0],v["lastMessage"][1],v["lastMessage"][2],v["lastMessage"][3],v["lastMessage"][4]) # getting the date of the last message
                expire = datetime.utcnow() + timedelta(minutes=30) # 30 minutes before the date now
                conditions = [lastMessageDate.year == expire.year, lastMessageDate.month == expire.month, lastMessageDate.day == lastMessageDate.day, lastMessageDate.hour == expire.hour, lastMessageDate.minute == expire.minute]
                if all(conditions): 
                    deleteList.append(k) # appends the channel to the delete list 
                    helpers = v["helpers"]
                    if len(helpers) == 0:
                        pass
                    else:
                        highest = 0
                        for d, e in helpers.items(): # caclulating the person who sent the most messages in the channel
                            if d > highest:
                                helper = e
                                highest = d
                    helper = guild.get_member(helper)                       

                    amount = BASE_REWARD # Since no rating is given we just give the user the base reward
                    await self.addExp(helper, amount, ctx.guild)
                    channel = self.bot.get_channel(int(k))
                    message = await channel.fetch_message(int(v["messageId"])) # messageId that was stored
                    guild = message.guild
                    await message.unpin() # unpins the message
                    await self.markAsDormant(channel) #Marks as dormant
            for k in deleteList: 
                del self.questions[k] # deletes from database

        async def cooldown(self, member: discord.Member, cdRole: discord.Role):
            global cooldownTime
            await member.add_roles(cdRole)
            await asyncio.sleep(cooldownTime)
            await member.remove_roles(cdRole)

        async def markAsDormant(self, channel: discord.TextChannel): # This is to mark a channel as dormant
            
            cur.execute("SELECT guild_id, channel_id FROM help_channels")
            records = cur.fetchall()
            valid = False
            for g, c in records: # Guild, channel
                if c == channel.id: # checking if the channel stored in the database is the same as the channel given to the procedure?
                    valid = True
                    guild_id = g
                    break
            if not valid: # If there is no record of the channel in our list then we raise an error
                raise ValueError("Channel is not in help_channels!!")
        
            dormantEmbed = discord.Embed(title="This help channel is dormant.", description="If you need help look at the avaliable channels category for more do the \
                                command /howtogethelp!", colour = 0xff2b2b)         
            cur.execute("SELECT dormantCategoryId, avaliableCategoryId, cooldownRoleId FROM schoolGuilds WHERE guildID = ?", (guild_id,)) # Gets the info from the guild 
            guild = self.bot.get_guild(int(guild_id))
            record = cur.fetchone()
            dormant = guild.get_channel(record[0])
            avaliable = guild.get_channel(record[1])
            cdRole = guild.get_role(record[2])

            cur.execute("SELECT studentRoleId FROM schoolGuilds WHERE guildID = ?", (guild_id,))
            role = cur.fetchone()
            sRole = guild.get_role(int(role[0]))
            overwrites= {sRole: discord.PermissionOverwrite(read_messages=True, send_messages=False)} # Students shouldnt be able to send messages but should be able to read messages
            await channel.edit(category=dormant, overwrites=overwrites)# Moves channel to the dormant category
            await channel.send(embed=dormantEmbed) # sends the "This channel is dormant" embed
                        





        async def addExp(self, helper, amount, guild, natural=True):
            global BASE_REWARD
            
            cur.execute(f"SELECT * FROM helpLevels WHERE memberId = {helper.id} AND guildId = {guild.id}")
            record = cur.fetchone() # This will be all the data or help levels.
            if record is None: # If there is no record we will make a new one
                cur.execute("INSERT INTO helpLevels VALUES (?,?,?,?,?)", (helper.id, guild.id, 0,0,1))
                record = (helper.id, guild.id, 0,0,1) #  
            exp = record[2] 
            exp+=amount # 
            level = baseLevel = record[4] # level before we do anything
            helped = record[3]
            if natural: # If the /exp command wasn't used
                helped+=1 
            leveledUp=False
            while exp >= 1000: #Means they have leveled up
                level +=1 # 
                exp -=1000
                leveledUp = True
            levelDifference = level - baseLevel # How many levels this person has gone up
            if leveledUp: 

                await helper.create_dm()
                name = helper.name + helper.discriminator # EliteNarNar + #7573
                embed = discord.Embed(title="You leveled up!", description=f"You are now level **{level}**", colour=0x00FF00)
                embed.set_thumbnail(url=helper.avatar_url)
                await helper.dm_channel.send(embed=embed) # Sends image showing that person has leveled up

                if level <=100: # Make sure the level is smaller than 100 because we only have roles for level 1 -100
                    
                    if level > 9:
                        roleLevel = (math.floor(level/10))*10 if level!=100 else 10 # rounding to the nearest 10
                        baseRoleLevel = (math.floor(baseLevel/10))*10  
                        if roleLevel == baseRoleLevel: # Title doesnt change
                            pass
                        else:
                            cur.execute(f"SELECT roleId FROM helpRoles WHERE guildId = {guild.id} ORDER BY level ASC") # We fetch levels in ascending order
                            roles = cur.fetchall() # selects the roleIds
                            addIndex = (roleLevel//10)-1 # Position in the list
                            removeIndex = (baseLevel//10)-1 if baseRoleLevel > 9 else None
                            addRole = guild.get_role(roles[addIndex][0])

                            await helper.add_roles(addRole)
                            if removeIndex is not None:
                                removeRole = guild.get_role(roles[removeIndex][0]) 
                                await helper.remove_roles(removeRole)
                            print(addIndex)
                            print(addRole)
                            print(removeIndex)
                            try:
                                print(removeRole) 
                            except:
                                pass                          





            cur.execute(f"UPDATE helpLevels SET XP = {exp}, peopleHelped = {helped}, level = {level} WHERE memberId = {helper.id}", ) # Updates with the new data
            con.commit() # commit changes



        async def getRankImage(self,member: discord.Member, exp,  level, total, guild):
            def drawProgressBar(d, x, y, w, h, progress, bg="black", fg="#a400fc"):
                # draw background
                d.ellipse((x+w, y, x+h+w, y+h), fill=bg)
                d.ellipse((x, y, x+h, y+h), fill=bg)
                d.rectangle((x+(h/2), y, x+w+(h/2), y+h), fill=bg)

                # draw progress bar
                w *= progress
                d.ellipse((x+w, y, x+h+w, y+h),fill=fg)
                d.ellipse((x, y, x+h, y+h),fill=fg)
                d.rectangle((x+(h/2), y, x+w+(h/2), y+h),fill=fg)

            
            cur.execute("SELECT level, roleId FROM helpRoles WHERE guildId = ? ORDER BY level DESC", (guild.id,))
            records = cur.fetchall()
            title = None
            print(level)
            if level > 9:
                roleLevel = str(level)
                roleLevel = roleLevel[0]
                roleLevelIndex = 10 - int(roleLevel)-1              
                role = guild.get_role(records[roleLevelIndex][1])
                title=role.name
            

            if title is None:
                title = ""
            cur.execute(" SELECT level, memberId FROM helpLevels WHERE guildId = ? ORDER BY level DESC", (guild.id,))
            records = cur.fetchall()
            counter=1
            for k, v in records:
                if v == member.id:
                    position = counter
                    break
                counter+=1
            
            size = width, height = 900, 200
            image = Image.new("RGB", size, "#342e38")
            image = image.convert("RGBA")

            
            font = ImageFont.truetype("resources/fonts/impact.ttf",40)
            rankfont = ImageFont.truetype("resources/fonts/light.ttf",30)
            titlefont = ImageFont.truetype("resources/fonts/med.ttf",27)
            
            draw = ImageDraw.Draw(image)
            #draw.rounded_rectangle([10, 20, width-300, height-20], fill=(74,74,74, 355))
            draw.rounded_rectangle([10, 20, width-300, height-20], fill=(74,74,74, 200), width=3,radius=20)
            draw.rounded_rectangle([650, 20, width-30, height-20], fill=(74,74,74,200), width=3,radius=20)
            
            
            buffer_avatar = io.BytesIO()
            avatar_asset = member.avatar_url_as(format='jpg', size=128) # read JPG from server to buffer (file-like object)
            await avatar_asset.save(buffer_avatar) 
            buffer_avatar.seek(0)
            progress=exp/1000
            # read JPG from buffer to Image
            avatar_image = Image.open(buffer_avatar)
            avatar_image = avatar_image.resize((128,128))
            circle_image = Image.new("L", (128, 128))
            circle_draw = ImageDraw.Draw(circle_image)
            circle_draw.ellipse((0,0, 128,128), fill=255)
            image.paste(avatar_image, (20,35), circle_image)
            name = member.name + "#"+member.discriminator
            draw.multiline_text((175,35), name, font=font, fill=(31, 24, 171))
            draw.multiline_text((175,90), title, font=titlefont, fill=(0, 255, 242))
            draw.multiline_text((465,100), f"{exp}/1000", font=rankfont, fill=(164, 0, 252) )
            draw.multiline_text((662,50), f"RANK: #{position}", font=rankfont, fill=(0, 166, 255) ) 
            draw.multiline_text((662,90), f"Level: {level}", font=rankfont, fill=(0, 166, 255))
            draw.multiline_text((662,130), f"People helped: {total}", font=rankfont, fill=(0, 166, 255))
            draw = drawProgressBar(draw, 155,135, 400, 25, progress, )
            image.resize((1350,300))
            buffer_output = io.BytesIO()
            
            
            image.save(buffer_output, "PNG")
            buffer_output.seek(0)
            return buffer_output






    
def setup(bot):
    bot.add_cog(Help(bot))
