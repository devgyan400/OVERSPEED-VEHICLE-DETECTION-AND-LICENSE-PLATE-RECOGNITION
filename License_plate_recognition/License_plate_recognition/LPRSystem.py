import numpy as np
import cv2
import  imutils
import pytesseract

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
    cnts, hierarchy = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[-2:]

    for i in cnts:
        if cv2.contourArea(i) > areaTH:
            peri = cv2.arcLength(i, True)
            approx = cv2.approxPolyDP(i, 0.02 * peri, True)
            if (len(approx) == 4):

                x,y,w,h = cv2.boundingRect(approx)
                licPlateImgF = imutils.resize(imgFile[y:y+h, x:x+w], width=200)

                #RUN TESSERACT OCR ON IMAGE-------------------------------------
                textTemp = pytesseract.image_to_string(licPlateImgF, config=config)

                if (len(textTemp)>=10):

                    cv2.rectangle(imgFile, (x, y), (x + w, y + h), (0,255,0), 2)
                    #cv2.imshow('Contour Detection', imgFile)

                    licNoF = ""
                    for i in textTemp:
                        if (i.isalnum() == True):
                            licNoF += i.upper()
                    break
    return licNoF,licPlateImgF, imgFile


def viewResults(imgFile, contourImg, crop_image, lic_no):
    cv2.imshow("Original Image", imutils.resize(imgFile, width=540))
    cv2.imshow("Contour Detected", imutils.resize(contourImg, width=540))
    cv2.imshow("License Plate",crop_image)
    print("License Number : ", lic_no)
    cv2.waitKey(0)

#VARIABLES----------------------------------------------------------------------
config = ('-l eng --oem 1 --psm 3')                     #TESSERACT CONFIGURATION
imageOriginal = cv2.imread('test.jpg')                  #LOAD THE IMAGE
licPlateImage = None
licNo  = None


#GET LICENSE PLATE--------------------------------------------------------------
licNo,licPlateImg, contourDetected = getLicenseNo(imageOriginal)

#DISPLAY OUTPUT-----------------------------------------------------------------
viewResults(imageOriginal, contourDetected, licPlateImg, licNo)
