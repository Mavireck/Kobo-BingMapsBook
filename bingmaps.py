BingMapsAPIKey = "An7FztQjFiWM6uCIoSGOZMx3d5r7DF3h9nUKHVVQHlg8sf-W9Mw8idQhG70X3-rx"
imagerySet = "CanvasGray"
#centerPoint = "47.610679194331169,-122.10788659751415"
#centerPoint = "Eiffel Tower,Paris, France"
centerPoint="48.858352497048735,2.29422043272987"
zoomLevel=16
borderSize=80
percentage_overlap = 0.10
number_of_images_each_direction = 3   #Keep this number reasonnable (I would say do not go over 4 or 5 images)

################################################################################

import requests
import sys
#from io import BytesIO
import os
import json
from PIL import Image, ImageFont
sys.path.append('../Python-Screen-Stack-Manager')
import pssm
import pssmObjectsLibrairy as POL
import platform
import time
if platform.machine() in ["x86","AMD64","i686","x86_64"]:
    # If it is a non-ARM device, it is likely to be used on a computer -> emulator
    # TODO : make a better test (get the device's precise name for instance or something like that)
    import pssm_opencv as pssm_device
else:
    import pssm_kobo as pssm_device


def quit(*args):
    print("Quitting")
    screen.stopListenerThread()
    if not pssm_device.isEmulator:
        pssm_device.do_screenDump_restore()
    return False

def changeDirection(objId,objData):
    global last_displayed_map_ID
    direction = objData
    print(direction, " - ", last_displayed_map_ID)
    if direction == "left":
        if not is_extremeLeft(last_displayed_map_ID):
            last_displayed_map_ID -= 1
            display_mapImage(last_displayed_map_ID)
    if direction == "right":
        if not is_extremeRight(last_displayed_map_ID):
            last_displayed_map_ID += 1
            display_mapImage(last_displayed_map_ID)
    if direction == "up":
        if not is_extremeUp(last_displayed_map_ID):
            last_displayed_map_ID += (1+2*number_of_images_each_direction)
            display_mapImage(last_displayed_map_ID)
    if direction == "down":
        if not is_extremeDown(last_displayed_map_ID):
            last_displayed_map_ID -= (1+2*number_of_images_each_direction)
            display_mapImage(last_displayed_map_ID)
    else:
        return None

def is_extremeLeft(index):
    return index%(1+2*number_of_images_each_direction)==0

def is_extremeRight(index):
    return is_extremeLeft(index+1)

def is_extremeDown(index):
    return index<(1+2*number_of_images_each_direction)

def is_extremeUp(index):
    return index>=(1+2*number_of_images_each_direction)*(2*number_of_images_each_direction)

def get_Coordinates(direction,bbox):
    p = percentage_overlap
    print("Being given direction : ",direction)
    if direction == "up":
        return [(1-p)*bbox[0]+p*bbox[2],0.5*bbox[1]+0.5*bbox[3]]
    if direction == "down":
        return [p*bbox[0]+(1-p)*bbox[2],0.5*bbox[1]+0.5*bbox[3]]
    if direction == "left":
        return [0.5*bbox[0]+0.5*bbox[2],(1-p)*bbox[1]+p*bbox[3]]
    if direction == "right":
        return [0.5*bbox[0]+0.5*bbox[2],p*bbox[1]+(1-p)*bbox[3]]
    else:
        print("error getting coordinates")
        return None

def get_Image(centerPoint_call,image=True,metadata=True):
    url = "https://dev.virtualearth.net/REST/v1/Imagery/Map/" + imagerySet + "/" + centerPoint_call + "/" + str(zoomLevel) +"?"
    data = {'mapSize': widthHeight,
        'zoomLevel':zoomLevel,
        'mapLayer':'Basemap,Buildings',
        'format':'jpeg',
        'mmd':"0",
        'key':BingMapsAPIKey}
    data2={'mapSize': widthHeight,
        'mapLayer':'Basemap,Buildings',
        'format':'jpeg',
        'mmd':"1",
        'key':BingMapsAPIKey}
    result = []
    if image:
        requested_image = requests.get(url, params = data)
        result.append(requested_image.content)
    if metadata:
        requested_image_metadata = requests.get(url, params = data2)
        result.append(requested_image_metadata.content)
    return result

def get_bbox(metadata):
    json_decoded = json.loads(metadata.decode('utf-8'))
    return json_decoded["resourceSets"][0]["resources"][0]["bbox"]

def save_img(content,name):
    with open(name+save_as, 'wb') as f:
        f.write(content)
    return True

def get_Index(ligne,colonne):
    return (number_of_images_each_direction*2+1)*ligne + colonne

def get_allImages():
    #First, get the coordinates of the center image
    metadata = get_Image(centerPoint,image=False,metadata=True)[0]
    bbox = get_bbox(metadata)
    #First, we go back to image 0 (so : left left ... left, then up up ... up.
    for i in range(number_of_images_each_direction):
        new_centerPoint = get_Coordinates("left",bbox)
        centerPointStr = str(new_centerPoint[0])+","+str(new_centerPoint[1])
        metadata = get_Image(centerPointStr,image=False,metadata=True)[0]
        bbox = get_bbox(metadata)
    for i in range(number_of_images_each_direction):
        new_centerPoint = get_Coordinates("up",bbox)
        centerPointStr = str(new_centerPoint[0])+","+str(new_centerPoint[1])
        metadata = get_Image(centerPointStr,image=False,metadata=True)[0]
        bbox = get_bbox(metadata)
    #Then we download all the images
    ligne = 0
    colonne = 0
    last_direction = "right"
    while ligne < number_of_images_each_direction*2+1:
        print("Downloading with ",ligne,"-", colonne)
        #time.sleep(0.1)
        #Download the image and its metadata
        [image,metadata] = get_Image(centerPointStr,image=True,metadata=True)
        #Save the image
        save_img(image,str(get_Index(ligne,colonne)))
        if colonne%(number_of_images_each_direction*2) == 0 and last_direction=="right" and colonne!=0:
            #Get the new centerPoint
            bbox = get_bbox(metadata)
            new_centerPoint = get_Coordinates("down",bbox)
            centerPointStr = str(new_centerPoint[0])+","+str(new_centerPoint[1])
            #we are at the extreme right, we can go down one line then change direction
            print("down and left")
            ligne += 1
            last_direction = "left"
        elif colonne%(1+2*number_of_images_each_direction)==0 and last_direction =="left":
            #Get the new centerPoint
            bbox = get_bbox(metadata)
            new_centerPoint = get_Coordinates("down",bbox)
            centerPointStr = str(new_centerPoint[0])+","+str(new_centerPoint[1])
            #we are at the extreme left, we can go down one line then change direction*
            print("down and right")
            ligne += 1
            last_direction = "right"
        else:
            #Get the new centerPoint
            bbox = get_bbox(metadata)
            new_centerPoint = get_Coordinates(last_direction,bbox)
            centerPointStr = str(new_centerPoint[0])+","+str(new_centerPoint[1])
            #Change column index
            if last_direction == "left":
                colonne -= 1
            else:
                colonne += 1
    return None


def display_mapImage(name):
    print("displaying ",name)
    print(" ")
    opened_image = Image.open(str(name)+save_as).convert("L").rotate(270,expand=True)
    maps_object = pssm.pillowImgToScreenObject(opened_image,0,borderSize)
    maps_object.onclickInside=None
    maps_object.tags.add("map")
    maps_object.data=last_displayed_map_ID   #The index of the center image
    screen.addObj(maps_object)

############################### - MAIN - #######################################
#Declare the Screen Stack Manager
screen = pssm.ScreenStackManager(pssm_device,'Main')
#Attach listener thread
screen.startListenerThread(grabInput=True)
if not pssm_device.isEmulator:
    # Take a screenshot
    pssm_device.do_screenDump()
#Clear and refresh the screen
screen.clear()
screen.refresh()
# Create a blank canvas
screen.createCanvas()

nb_imgs = number_of_images_each_direction
path_save="map.jpg"
last_displayed_map_ID = (nb_imgs)*(1+2*nb_imgs)+nb_imgs  #The index of the center image
save_as=".jpg"
path_save_metadata="metadata.json"
width=min(2000,screen.height-borderSize)
height=min(1500,screen.width)
widthHeight = str(width) +","+ str(height)
x0=0
x1=int(screen.width/2)
y0=0
y1=int(screen.height/4)

Merri_regular = os.path.join("fonts", "Merriweather-Regular.ttf")
small_font_size = int(pssm_device.screen_height/52)
small_font = ImageFont.truetype(Merri_regular, small_font_size)

#Keep in mind everything is rotated 90 degrees
down_object = POL.rectangle(x0,y1+borderSize,x1,2*y1,fill=255,outline=255)
up_object = POL.rectangle(x1+1,y1+borderSize,x1,2*y1,fill=255,outline=255)
left_object = POL.rectangle(x0,borderSize,2*x1,y1-borderSize,fill=255,outline=255)
right_object = POL.rectangle(0,3*y1,2*x1,y1,fill=255,outline=255)
left_object.onclickInside = changeDirection
right_object.onclickInside = changeDirection
up_object.onclickInside = changeDirection
down_object.onclickInside = changeDirection
left_object.data="left"
right_object.data="right"
up_object.data="up"
down_object.data="down"
screen.addObj(left_object)
screen.addObj(right_object)
screen.addObj(up_object)
screen.addObj(down_object)

back_icon_object = POL.icon("back",0,0,icon_size=borderSize)
back_icon_object.onclickInside = quit
screen.addObj(back_icon_object)


if not os.path.exists("0.jpg"):
    disclaimer_button = POL.rectangle(0,borderSize+2,screen.width,300,outline=255)
    disclaimer_button = POL.add_centeredText(disclaimer_button,"Downloading...\n Please wait a few seconds",small_font)
    screen.addObj(disclaimer_button)
    print("files do not exist")
    get_allImages()
    screen.removeObj(disclaimer_button.id)


display_mapImage(last_displayed_map_ID)

