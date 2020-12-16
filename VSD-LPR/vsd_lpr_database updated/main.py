from threading import Thread
from vsd import vsdMain
from lpr import lprLooped
from store_data import storeDataMain, connectToFirebase

#connect to firebase and cloud FireStore
if connectToFirebase():
    print ("Connected to Cloud FireStore and Cloud storage")
    #creating threads
    t1 = Thread(target = vsdMain)
    t2 = Thread(target = lprLooped)
    t3 = Thread(target = storeDataMain)
    #start threads
    t1.start()
    t2.start()
    t3.start()
else:
    print ("Unable to Connect")
