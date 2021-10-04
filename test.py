names = ["Ash", "Birch", "Cedar", "Dragon", "Elm", "Fir","Garjan", "Hazel", "Ivorypalm", "Juniper", "Kapok", "Locust", "Mombin","Nutmeg", "Oak", "Palm","Sapel", \
    "Teak", "Upas", "Wingnut", "Yew", "Zelkova"]
ROWS = 3
rem = len(names) %ROWS
if rem == 0:
  columns = (len(names) /ROWS)  
else:
  columns = (len(names)//ROWS) + 1
  students = ""
  names.sort()
  total = 0
  for name in names:
    maxLength = len(name) #getting the longest name
    total+= len(name)

averageLength= total/ len(names)
upperQuartile = (maxLength + averageLength) / 2 # Finding the upper quartile which will be a reasonable amount of space between each columm
totalCharacters = upperQuartile + 4 

for x in range(columns):
  studentrow = ""
  for y in range(ROWS):
      print(y)
      index = x+(ROWS*(y))
      member = names[index]
      spaces = int(totalCharacters - len(member)) # This will make sure that the correct amount of spaces will be added to make the columns inline
      whitespace = ""
      whitespace += " "*spaces

      studentrow+= name+whitespace
  students += studentrow + "\n"
print(students)
