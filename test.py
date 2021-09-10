from PIL import Image, ImageDraw

# Open template and get drawing context
im = Image.open('resources/images/xpbar.png').convert('RGB')
draw = ImageDraw.Draw(im)

# Cyan-ish fill colour
color=(98,211,245)

# Draw circle at right end of progress bar
x, y, diam =  592, 8, 34 ## 592
draw.ellipse([x,y,x+diam,y+diam], fill=color)

# Flood-fill from extreme left of progress bar area to behind circle
ImageDraw.floodfill(im, xy=(14,24), value=color, thresh=40)

# Save result
im.show()