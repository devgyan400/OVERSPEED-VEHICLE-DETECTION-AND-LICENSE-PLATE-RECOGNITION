import numpy as np
import cv2
import imutils
import pytesseract

#function to generate canny image
def autocanny(image, sigma=0.33):
    v = None
    lower, upper = None, None
    edged = None

    v = np.median(image)
    lower = int(max(0, (1.0 - sigma)*v))
    upper = int(min(255, (1.0 - sigma)*v))
    edged = cv2.Canny(image, lower, upper)

    return edged

#Check if contour is a probable license plate
def checkProbLic(cnt):
    lenfactor = 0.3 #important parameter
    quadFactor = 0.05 #important parameter
    ratio_llimit = 3 #important parameter
    ratio_ulimit = 6 #important parmeter
    quad = False
    parallel = False
    probLicPlate = False

    perimeter = None
    corners = None
    side1, side2, side3, side4 = None, None, None, None

    perimeter = cv2.arcLength(cnt, True)
    corners = cv2.approxPolyDP(cnt, quadFactor*perimeter, True)
    if len(corners) == 4:
        quad = True

    #check if contour is a quadrilateral / almost parallelogram
    if quad:
        corners = (corners.reshape(4,2)).tolist()
        side1 = np.sqrt((corners[0][0] - corners[1][0])**2 + (corners[0][1] - corners[1][1])**2)
        side2 = np.sqrt((corners[1][0] - corners[2][0])**2 + (corners[1][1] - corners[2][1])**2)
        side3 = np.sqrt((corners[2][0] - corners[3][0])**2 + (corners[2][1] - corners[3][1])**2)
        side4 = np.sqrt((corners[3][0] - corners[0][0])**2 + (corners[3][1] - corners[0][1])**2)

        if side1*(1-lenfactor) < side3 < side1*(1+lenfactor):
            if side2*(1-lenfactor) < side4 < side2*(1+lenfactor):
                parallel = True

    #check if the ratio of width to height is somewhat similar to a license plate
    if parallel:
        if ratio_llimit < (max(side1, side2) / min(side1, side2)) < ratio_ulimit:
            probLicPlate = True

    return probLicPlate

#correct the perspective of license plate image
def correctPerspective(cnt):
    #declaring variables
    resizefactor = None
    quadFactor = 0.05 #should be same as in checkproblic
    perimeter = None
    corners = None
    tl, tr, br, bl = None, None, None, None
    widthTop, widthBottom = None, None
    heightLeft, heightRight = None, None
    licWidth, licHeight = None, None
    canvas = None
    transformMatrix = None

    resizefactor = original.shape[0]/resizeHeight

    #get the 4 corners in order
    perimeter = cv2.arcLength(cnt, True)
    corners = cv2.approxPolyDP(cnt, quadFactor*perimeter, True)
    corners = (corners.reshape(4,2)*resizefactor).astype(int).tolist()

    tl = min(corners, key = lambda x: x[0]+x[1])
    tr = max(corners, key = lambda x: x[0]-x[1])
    br = max(corners, key = lambda x: x[0]+x[1])
    bl = min(corners, key = lambda x: x[0]-x[1])

    corners = np.array([tl, tr, br, bl], dtype='float32').reshape(4,2)

    #get the size of corrected license image
    widthTop = np.sqrt((tl[0] - tr[0])**2 + (tl[1] - tr[1])**2)
    widthBottom = np.sqrt((bl[0] - br[0])**2 + (bl[1] - br[1])**2)
    heightLeft = np.sqrt((tl[0] - bl[0])**2 + (tl[1] - bl[1])**2)
    heightRight = np.sqrt((tr[0] - br[0])**2 + (tr[1] - br[1])**2)

    licWidth = int((widthTop + widthBottom)/2)
    licHeight = int((heightLeft + heightRight)/2)

    #transform the license image and put on campus
    canvas = np.array([
        [0,0],
        [licWidth-1, 0],
        [licWidth-1, licHeight-1],
        [0, licHeight-1]], dtype='float32')

    transformMatrix = cv2.getPerspectiveTransform(corners, canvas)
    canvas = cv2.warpPerspective(original, transformMatrix, (licWidth, licHeight))

    return canvas

def getBoundingBox(cnt):
    resizefactor = None
    boundingBox = None
    x, y, w, h = None, None, None, None

    resizefactor = original.shape[0]/resizeHeight

    boundingBox = cv2.boundingRect(cnt)
    x, y, w, h = [int(i*resizefactor) for i in boundingBox]

    canvas = original[y:y+h, x:x+w]

    return canvas

def getBinary(img):
    binImg = None

    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binImg = cv2.threshold(img, 0, 255, cv2.THRESH_OTSU)[1]

    if int(np.median(binImg)) == 0:
        binImg = cv2.bitwise_not(binImg)

    return binImg

def recognizeLic(probLicImages):
    finalLicNo = None
    finalLicImage = None
    config = ('-l eng --oem 1 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')

    for licImg in probLicImages:
        licNoTemp = pytesseract.image_to_string(licImg, config=config)
        if licNoTemp:
            if finalLicImage is None:
                finalLicNo = licNoTemp
                finalLicImage = licImg
            elif len(licNoTemp) > len(finalLicNo):
                finalLicNo = licNoTemp
                finalLicImage = licImg

    return finalLicNo, finalLicImage


#-----------------------------------------------------------------------

def lprMain(imgsrc):
    #Declaring variables
    global original
    global resizeHeight
    img = None
    gray = None
    blurred = None
    edged = None
    cnts = None
    roiList = None
    roidrawn = None
    probLicImages = None
    finalLicNo = None
    finalLicImage = None

    #apply filters on image
    original = imgsrc.copy()
    img = imutils.resize(original.copy(), height=resizeHeight)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.bilateralFilter(gray, 10, 30, 30)
    edged = autocanny(blurred)

    #find the contours for opencv4 and opencv3
    if (int(cv2.__version__[0]) > 3):
        cnts = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    else:
        cnts = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[1]

    #ignore the small contours
    cnts = [i for i in cnts if cv2.arcLength(i, True) > 200]

    #get the convex hull of each contour (smallest bounding polygon)
    cnts = [cv2.convexHull(i) for i in cnts]

    #check if contour is a probable license plate
    roiList = [i for i in cnts if checkProbLic(i)]

    #draw the probable license plates on image
    roidrawn = cv2.drawContours(img.copy(), roiList, -1, (0,255,0), 3)

    #IMPORTANT
    #USE ONLY ONE either correctPerspective or getBoundingBox
    #The correctPerspective function might be a bit slow,
    #for most cases, just getting the bounding box is enough

    probLicImages = [correctPerspective(licCnt) for licCnt in roiList]
    #probLicImages = [getBoundingBox(licCnt) for licCnt in roilList]

    #binarize the license licImage
    probLicImages = [getBinary(licImg) for licImg in probLicImages]

    #recognize license number using tesseract
    finalLicNo, finalLicImage = recognizeLic(probLicImages)

    #print and display results
    print('License Number: {}'.format(finalLicNo))
    #cv2.imshow('Orignal', imutils.resize(original, height=resizeHeight))
    #cv2.imshow('Gray', gray)
    #cv2.imshow('Blurred', blurred)
    #cv2.imshow('Autocanny', edged)
    cv2.imshow('Car', imutils.resize(roidrawn, height=360))

    if finalLicImage is not None:
        print('Displaying Image...')
        cv2.imshow('Lic', finalLicImage)
    else:
        print("Unable to detect license Plate\nCan't display image.")

    cv2.waitKey(0)
    cv2.destroyAllWindows()

#-----------------------------------------------------------------------

#globals
resizeHeight = 600 #important parameter
original = None #the original image will be stored in this

if __name__ == '__main__':
    filepath = 'test_images/11.jpg'
    lprMain(cv2.imread(filepath))
