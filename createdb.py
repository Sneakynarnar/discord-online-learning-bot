import sqlite3

con = sqlite3.connect("resources/databases/schooldata.db")
cur = con.cursor()
#cur.execute("DELETE FROM help_channels")
#cur.execute("DELETE FROM subjects")
#cur.execute("DROP TABLE helpLevels")
#cur.execute("DROP TABLE lessons")



#cur.execute("DELETE FROM helpRoles WHERE guildId = 899703139840708668")

cur.execute("ALTER TABLE schoolGuilds ADD managerChatId integer")
#cur.execute("CREATE TABLE lessons (classId integer PRIMARY_KEY, guildId integer, name text, dateTime datetime, subject text, teacherId integer, repeatWeekly bool, description text, lessonDuration integer, VC integer, TC, integer, embed integer)")
#cur.execute("CREATE TABLE studentLessons (studentId integer, classId integer, guildId integer)")
#cur.execute("CREATE TABLE helpRoles (roleId integer PRIMARY_KEY, guildId integer,level integer ) ")
#cur.execute("DROP TABLE scoolGuilds;")
##cur.execute("CREATE TABLE schoolGuilds (guildID integer PRIMARY_KEY, schoolName text, schoolAbreviation text, studentRoleId integer, teacherRoleId integer, managerRoleId integer, avaliableCategoryId integer, dormantCategoryId integer)")
con.commit()
cur.close()
