import cv2
import imutils
import dlib
from datetime import datetime
import os
import numpy as np
#import the variables from data_list file
from data_list import overSpeedArr

#-----------------------------------------------------------------------

#function to clear portion of an image for faster processing
def blackout(image):
    xBlack = 360
    yBlack = 300
    triangle_cnt = None
    triangle_cnt2 = None
    triangle_cnt = np.array( [[0,0], [xBlack,0], [0,yBlack]] )
    triangle_cnt2 = np.array( [[resizeWidth,0], [resizeWidth-xBlack,0], [resizeWidth,yBlack]] )
    cv2.drawContours(image, [triangle_cnt], 0, (0,0,0), -1)
    cv2.drawContours(image, [triangle_cnt2], 0, (0,0,0), -1)
    return image

#function to save car image
def saveCarImage(speed,carImage):
    now = None
    nameCurTime = None
    link = None
    now = datetime.today().now()
    nameCurTime = now.strftime("%d-%m-%Y-%H-%M-%S-%f")
    link = 'overspeeding/'+nameCurTime+'.jpeg'
    cv2.imwrite(link,carImage, [int(cv2.IMWRITE_JPEG_QUALITY), 70])

#function to calculate speed
def estimateSpeed(carID):
    markGap = 50   #distance in metres between the markers
    fpsFactor = 10 #to compensate for slow processing
    timeDiff = None
    speed = None
    timeDiff = (endTracker[carID]-startTracker[carID]).total_seconds()
    speed = round(markGap/timeDiff*fpsFactor*3.6,2)
    return speed

#-----------------------------------------------------------------------

def vsdMain():
    print('\n----- Thread 1 -----')
    global carTracker
    global startTracker
    global endTracker
    carCascade = None
    video = None
    image = None
    frameTime = None
    resultImage = None
    frameCounter = None
    carID = None
    carIDtoDelete = None
    trackingQuality = None
    gray = None
    cars = None
    x, y, w, h = None, None, None, None
    xbar, ybar = None, None
    matchCarID = None
    currentCarID = None
    trackedPosition = None
    tx, ty, tw, th = None, None, None, None
    txbar, tybar = None, None
    tracker = None
    resizeWidth = 960 #resizeWidth of video frame
    resizeHeight = 540 #resizeHeight of video frame
    cropBegin = 240 #crop video frame from this point
    mark1 = 320 #mark to start timer
    mark2 = 440 #mark to end timer
    speedLimit = 10 #speedlimit
    #classifer for detecting cars
    carCascade = cv2.CascadeClassifier('files/HaarCascadeClassifier.xml')
    #get the video
    video = cv2.VideoCapture('files/test.mp4')
    #make directory to store over-speeding car images
    if not os.path.exists('overspeeding/'):
        os.makedirs('overspeeding/')
    #print the speed limit
    print('Speed Limit Set at {} Kmph'.format(speedLimit))
    frameCounter = 0 #initialize the frame counter
    currentCarID = 0 #id of last car to be added
    #start Tracking
    while True:
        image = video.read()[1]
        if type(image) == type(None):
            break
        frameTime = datetime.now()
        image = cv2.resize(image, (resizeWidth, resizeHeight)) #[cropBegin:resizeHeight,0:resizeWidth]
        #resultImage = blackout(image)
        resultImage = image.copy()
        #cv2.line(resultImage,(0,mark1),(resizeWidth,mark1),(0,0,255),2)  #uncomment to view video
        #cv2.line(resultImage,(0,mark2),(resizeWidth,mark2),(0,0,255),2)  #uncomment to view video
        frameCounter = frameCounter + 1
        #delete CarID's not in frame
        carIDtoDelete = []
        for carID in carTracker.keys():
            trackingQuality = carTracker[carID].update(image)
            if trackingQuality < 7:
                carIDtoDelete.append(carID)
        for carID in carIDtoDelete:
            carTracker.pop(carID, None)
        #track every 60th frame
        if (frameCounter%60 == 0):
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            #detect cars in frame
            cars = carCascade.detectMultiScale(gray, 1.1, 13, 18, (24, 24))
            for (_x, _y, _w, _h) in cars:
                #get position of a car
                x = int(_x)
                y = int(_y)
                w = int(_w)
                h = int(_h)
                xbar = x + 0.5*w
                ybar = y + 0.5*h
                matchCarID = None
                #if centroid of current car is near the centroid of another car
                #in the previous frame, then they are the same car
                for carID in carTracker.keys():
                    trackedPosition = carTracker[carID].get_position()
                    tx = int(trackedPosition.left())
                    ty = int(trackedPosition.top())
                    tw = int(trackedPosition.width())
                    th = int(trackedPosition.height())
                    txbar = tx + 0.5 * tw
                    tybar = ty + 0.5 * th
                    if (tx <= xbar <= (tx + tw)) and (ty <= ybar <= (ty + th)):
                        if (x <= txbar <= (x + w)) and (y <= tybar <= (y + h)):
                            matchCarID = carID
                if matchCarID is None:
                    tracker = dlib.correlation_tracker()
                    tracker.start_track(image, dlib.rectangle(x, y, x + w, y + h))
                    carTracker[currentCarID] = tracker
                    currentCarID = currentCarID + 1
        for carID in carTracker.keys():
            trackedPosition = carTracker[carID].get_position()
            tx = int(trackedPosition.left())
            ty = int(trackedPosition.top())
            tw = int(trackedPosition.width())
            th = int(trackedPosition.height())
            #put bounding boxes
            #cv2.rectangle(resultImage, (tx, ty), (tx + tw, ty + th), (0, 255, 0), 2)  #uncomment to view video
            #cv2.putText(resultImage, str(carID), (tx,ty-5), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0), 1)  #uncomment to view video
            #check if a car has crossed mark1, if yes add startTracker for carID
            if carID not in startTracker and mark2 > ty+th > mark1 and ty < mark1:
                startTracker[carID] = frameTime
            #check if a car has crossed mark2, if yes, add endTracker to carID & estimate speed
            elif carID in startTracker and carID not in endTracker and mark2 < ty+th:
                endTracker[carID] = frameTime
                speed = estimateSpeed(carID)
                if speed > speedLimit:
                    print('Thread 1 : CAR-ID = {} | Speed = {} kmph | Overspeed'.format(carID, speed))
                    #save image of car
                    #saveCarImage(speed,image[ty:ty+th, tx:tx+tw])
                    #add data for license detection
                    overSpeedArr.append((frameTime, speed, image[ty:ty+th, tx:tx+tw]))
                else:
                    print('Thread 1 : CAR-ID = {} | Speed = {} kmph'.format(carID, speed))
        #Display each frame
        #cv2.imshow('result', resultImage)  #uncomment to view video
        #cv2.imshow('result', imutils.resize(resultImage, height=360))
        #if cv2.waitKey(33) == 27:                      #uncomment to view video
        #    break                                      #uncomment to view video
    #close the video
    #cv2.destroyAllWindows()                            #uncomment to view video

#-----------------------------------------------------------------------

carTracker = {}   #store tracking details of cars
startTracker = {} #store starting time of cars
endTracker = {}   #store ending time of cars

if __name__ == '__main__':
    vsdMain()
