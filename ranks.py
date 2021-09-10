

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io
import urllib.request
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

    return d
def createRankImage(username, exp, position, level, total,title):
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
    avatar_image = Image.open("resources/images/test.jpg")
    avatar_image = avatar_image.resize((128, 128))
    circle_image = Image.new("L", (128, 128))
    circle_draw = ImageDraw.Draw(circle_image)
    circle_draw.ellipse((0,0, 128,128), fill=255)
    image.paste(avatar_image, (20,35), circle_image)

    draw.multiline_text((175,35), username, font=font, fill=(0, 166, 255))
    draw.multiline_text((175,90), title, font=titlefont, fill=(0, 255, 242))
    draw.multiline_text((465,100), f"{exp}/1000", font=rankfont, fill=(164, 0, 252) )
    draw.multiline_text((655,50), f"RANK: #{position}", font=rankfont, fill=(0, 166, 255) ) 
    draw.multiline_text((655,90), f"Level: {level}", font=rankfont, fill=(0, 166, 255))
    draw.multiline_text((655,130), f"People helped: {total}", font=rankfont, fill=(0, 166, 255))


    draw = drawProgressBar(draw, 155,135, 400, 25, 0.75, )
    image.show()
    


createRankImage("EliteNarNar#0001", 750, 1,  60,1003,"Legendary Helper")