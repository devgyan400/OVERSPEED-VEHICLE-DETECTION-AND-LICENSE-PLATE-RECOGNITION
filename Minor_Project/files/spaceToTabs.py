import os

fin = open('Speed_Detection_saveCar.py', "rt")
data = fin.read()
data = data.replace("\t","    ")
fin.close()

fin = open('Speed_Detection_saveCar.py', "wt")
fin.write(data)
fin.close()
