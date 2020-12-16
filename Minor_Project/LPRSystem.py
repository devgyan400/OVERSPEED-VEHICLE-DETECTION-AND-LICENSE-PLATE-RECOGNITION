import numpy as np
import cv2
import  imutils
import pytesseract
import csv
import sqlite3
from twilio.rest import Client
import os

def licenseProgram(date,time,speed,imageLink):
    currentDate = date
    currentTime = time
    speed = speed
    imageOriginal = cv2.imread(imageLink)
    licPlateImage = None
    licNo  = None
    licenseError = None
    name = None
    contactNo = None
    dataValues = None
    msgSID = None

    #GET LICENSE PLATE---------------------------------------
    licNo,licPlateImg = getLicenseNo(imageOriginal)

    #RETREIVING VEHICLE OWNER DETAILS------------------------
    licenseError,name,contactNo = ownerDetails(licNo)

    #STORING DATA IN ANOTHER SQLITE DATABASE-----------------
    dataValues = [currentDate, currentTime, licNo, licenseError]
    storeData(dataValues,licPlateImg)

    #SENDIND SMS USING TWILIO API----------------------------
    if (licenseError == 0):
        try:
            msgSID = sendSMS(name,licNo,dataValues[0],dataValues[1],contactNo)
        except:
            pass

    #DISPLAY OUTPUT-----------------------------------------
    viewResults(imageOriginal,licPlateImg,licNo,name,contactNo,msgSID)

#RETURNS LICENSE PLATE NUMBER AND IMAGE-----------------------------------------
def getLicenseNo(imgFile):
    licNoF = None
    licPlateImgF = None

    #RESIZE THE IMAGE-----------------------
    resizeWidth = 1000
    if (imgFile.shape[1]>resizeWidth):
        imgFile = imutils.resize(imgFile, width=resizeWidth)

    #APPLY FILTERS ON IMAGE-----------------
    image = cv2.cvtColor(imgFile, cv2.COLOR_BGR2GRAY)
    image = cv2.bilateralFilter(image, 11, 17, 17)
    image = cv2.Canny(image, 170, 200)

    #FIND ALL CONTOURS----------------------
    cnts = cv2.findContours(image.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[0]

    #TAKE THE 10 LARGEST CONTOURS-----------
    cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:10]

    for i in cnts:
        peri = cv2.arcLength(i, True)
        approx = cv2.approxPolyDP(i, 0.02 * peri, True)
        if (len(approx) == 4):

            x,y,w,h = cv2.boundingRect(approx)
            licPlateImgF = imutils.resize(imgFile[y:y+h, x:x+w], width=200)

            #RUN TESSERACT OCR ON IMAGE------
            textTemp = pytesseract.image_to_string(licPlateImgF, config=config)

            if (len(textTemp)>=10):
                licNoF = ""
                for i in textTemp:
                    if (i.isalnum() == True):
                        licNoF += i.upper()
                break
    return licNoF,licPlateImgF

#FETCHES THE OWNER DETAILS OF THAT LICENSE PLATE--------------------------------
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

#STORES THE LICENSE DATA IN DATABASE--------------------------------------------
def storeData(row,licPlateImgF):
    filename = os.path.splitext(os.path.basename(imageLink))[0]
    link = 'overspeeding/cars/licenses/'+filename+'.jpeg'
    print(link)
    cv2.imwrite(link,licPlateImgF)
    cur.execute('CREATE TABLE IF NOT EXISTS LICENSEDATA (Date TEXT, Time TEXT, License TEXT, LicenseLink TEXT, LicenseError INTEGER)')
    cur.execute('INSERT INTO LICENSEDATA VALUES (?,?,?,?,?)',(row[0], row[1], row[2], link, row[3]))
    conn.commit()

#SEND SMS TO OWNER VIA TWILIO---------------------------------------------------
def sendSMS(name,lic_no,date,time,contactNo):
    # Your Account Sid and Auth Token from twilio.com/console
    # DANGER! This is insecure. See http://twil.io/secure
    account_sid = 'AC1cde836515a1799f790785c12fa30b12'
    auth_token = 'f2045bad8b6f1f70f54a5e39cfdd3666'
    client = Client(account_sid, auth_token)

    message = client.messages \
                    .create(
                         body="Mr/Ms {} your vehicle - License Number : {} has broken the speed limit on {} at {}. Please pay the fine at your nearest RTO.".format(name,lic_no,date,time),
                         from_='+12056274864',#ANURAG GUPTA's twilio phone number
                         to='+91'+str(contactNo)
                     )

    return message.sid

#DISPLAY RESULTS IN COMMAND LINE------------------------------------------------
def viewResults(imgFile,crop_image,lic_no,nameF,contactNoF,msgSID_F):
    cv2.imshow("Original Image", imutils.resize(imgFile, width=540))
    cv2.imshow("License Plate",crop_image)
    print("License Number : ", lic_no)
    print("Owner : ", nameF)
    print("Contact Number : ", contactNoF)
    print("Message SID (Twilio) : ", msgSID_F)
    cv2.waitKey(0)

if __name__ == '__main__':

    #VARIABLES----------------------------------------------
    config = ('-l eng --oem 1 --psm 3') #TESSERACT CONFIGURATION
    conn = sqlite3.connect('files/SDVR.sqlite') #CONNECT TO DATABAE
    cur = conn.cursor() #CURSOR TO FETCH RESULTS

    if not os.path.exists('overspeeding/cars/licenses/'):
        os.makedirs('overspeeding/cars/licenses/')

    cur.execute('SELECT Date, EndTime, Speed_kmph, ImageLink FROM SPEEDINGCAR')
    rowCar = cur.fetchone()
    if rowCar != None:
        date = rowCar[0]
        time = rowCar[1]
        speed = rowCar[2]
        imageLink = rowCar[3]
        licenseProgram(date, time, speed, imageLink)
