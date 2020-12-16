import numpy as np
import cv2
import  imutils
import pytesseract
import csv
from datetime import datetime
import sqlite3
from twilio.rest import Client

def getLicenseNo(imgFile):
    licNoF = None
    licPlateImgF = None

    #RESIZE THE IMAGE-----------------------------------------------------------
    resizeWidth = 960
    if (imgFile.shape[1]>resizeWidth):
        imgFile = imutils.resize(imgFile, width=resizeWidth)

    areaTH = (imgFile.shape[0]*imgFile.shape[1])//300

    #APPLY FILTERS ON IMAGE-----------------------------------------------------
    image = cv2.cvtColor(imgFile, cv2.COLOR_BGR2GRAY)
    image = cv2.bilateralFilter(image, 11, 17, 17)
    image = cv2.Canny(image, 170, 200)

    #FIND ALL CONTOURS----------------------------------------------------------
    cnts, hierarchy = cv2.findContours(image.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[-2:]

    for i in cnts:
        if cv2.contourArea(i) > areaTH:
            peri = cv2.arcLength(i, True)
            approx = cv2.approxPolyDP(i, 0.02 * peri, True)
            if (len(approx) == 4):

                x,y,w,h = cv2.boundingRect(approx)
                licPlateImgF = imutils.resize(imgFile[y:y+h, x:x+w], width=200)

                #RUN TESSERACT OCR ON IMAGE-------------------------------------
                textTemp = pytesseract.image_to_string(licPlateImgF, config=config)

                if (len(textTemp)>=6):
                    licNoF = ""
                    for i in textTemp:
                        if (i.isalnum() == True):
                            licNoF += i.upper()
                    break
    return licNoF,licPlateImgF

def ownerDetails(licNoF):
    licenseErrorF = 1
    nameF = None
    contactNoF = None

    cur.execute('SELECT Name, Contact_Number FROM VEHICLEOWNER WHERE License_Number = "{}"'.format(licNoF))
    rowLicense = cur.fetchone()
    if rowLicense != None:
        licenseErrorF = 0
        nameF = rowLicense[0]
        contactNoF = rowLicense[1]

    return licenseErrorF, nameF, contactNoF

def storeData(row,licPlateImgF):
    cur.execute('CREATE TABLE IF NOT EXISTS LICENSEDATA (Date TEXT, Time TEXT, License TEXT, LicenseError INTEGER)')
    cur.execute('INSERT INTO LICENSEDATA VALUES (?,?,?,?)',(row[0], row[1], row[2], row[3]))
    conn.commit()

def sendSMS(name,lic_no,date,time):
    account_sid = 'ACe36a4aa7552851e49fe050f704fcae63'
    auth_token = '44f37f12a2b28f0d4bfc65e7b95c87bf'
    client = Client(account_sid, auth_token)

    message = client.messages \
                    .create(
                         body="Mr/Ms {} your vehicle - License Number : {} has broken the speed limit on {} at {}. Please pay the fine at your nearest RTO.".format(name,lic_no,date,time),
                         from_='+18155818633',             # twilio phone number
                         to='+91'+str(contactNo)
                     )

    return message.sid

def viewResults(imgFile,crop_image,lic_no,nameF,contactNoF,msgSID_F):
    cv2.imshow("Original Image", imutils.resize(imgFile, width=540))
    try:
        cv2.imshow("License Plate",crop_image)
    except:
        pass
    print("License Number : ", lic_no)
    print("Owner : ", nameF)
    print("Contact Number : ", contactNoF)
    print("Message SID (Twilio) : ", msgSID_F)
    cv2.waitKey(0)

#VARIABLES----------------------------------------------------------------------
config = ('-l eng --oem 1 --psm 3')                     #TESSERACT CONFIGURATION
now = datetime.today().now()                            #GET CURRENT DATE AND TIME
currentDate = now.strftime("%d/%m/%Y")                  #EXTRACT CURRENT DATE
currentTime = now.strftime("%H:%M:%S")                  #EXTRACT CURRENT TIME
imageOriginal = cv2.imread('carback11.jpg')             #LOAD THE IMAGE
licPlateImage = None
licNo  = None
licenseError = None
name = None
contactNo = None
conn = sqlite3.connect('LPRSystem.sqlite')              #CONNECT TO DATABAE
cur = conn.cursor()                                     #CURSOR TO FETCH RESULTS
dataValues = None
msgSID = None

#GET LICENSE PLATE--------------------------------------------------------------
licNo,licPlateImg = getLicenseNo(imageOriginal)

#RETREIVING VEHICLE OWNER DETAILS-----------------------------------------------
licenseError,name,contactNo = ownerDetails(licNo)

#STORING DATA IN ANOTHER SQLITE DATABASE----------------------------------------
dataValues = [currentDate, currentTime, licNo, licenseError]
storeData(dataValues,licPlateImg)

#SENDIND SMS USING TWILIO API---------------------------------------------------
if (licenseError == 0):
    try:
        msgSID = sendSMS(name,licNo,dataValues[0],dataValues[1])
    except:
        pass

#DISPLAY OUTPUT-----------------------------------------------------------------
viewResults(imageOriginal,licPlateImg,licNo,name,contactNo,msgSID)
