import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime
from time import sleep
import cv2
import os
#import variables from data_list file
from data_list import licenseDataArr

#-----------------------------------------------------------------------

def connectToFirebase():
    global cred
    global db
    global bucket
    cred = credentials.Certificate('files/vsd-lpr-json-key.json')
    try:
        #firebase_admin.initialize_app(cred)
        firebase_admin.initialize_app(cred, {'storageBucket': 'vsd-lpr.appspot.com'})
        db = firestore.client()
        bucket = storage.bucket()
        return True
    except:
        return False

def storeDataMain():
    global db
    global bucket
    frameTime = None
    speed = None
    finalLicNo = None
    imgsrc = None
    frameTime_date = None
    frameTime_time = None
    imagePath = None
    blob = None
    licError = 0
    imageURL = None
    dataDict = None
    while True:
        if len(licenseDataArr) > 0:
            print('\n---------- Thread 3 ----------')
            frameTime, speed, finalLicNo, imgsrc = licenseDataArr.pop(0)
            frameTime_date = frameTime.strftime("%Y-%m-%d")
            frameTime_time = frameTime.strftime("%H: %M: %S")
            imagePath = frameTime.strftime("%Y-%m-%d-%H-%M-%S-%f")+'.jpeg'
            cv2.imwrite(imagePath, imgsrc, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            blob = bucket.blob(imagePath)
            blob.upload_from_filename(imagePath)
            imageURL = blob.public_url
            os.remove(imagePath)
            print('Thread 3 : Uploaded Vehicle Image')
            if finalLicNo == None:
                licError = 1
            dataDict = {
                        'deviceID': 1,
                        'date': frameTime_date,
                        'time': frameTime_time,
                        'speed': speed,
                        'licNo': finalLicNo,
                        'licError': licError,
                        'imageLink': imageURL
                        }
            db.collection(u'overspeed').add(dataDict)
            print('Thread 3 : Data Stored')
        else:
            sleep(5.0)

#-----------------------------------------------------------------------

cred = None
db = None
bucket = None

if __name__ == '__main__':
    pass
