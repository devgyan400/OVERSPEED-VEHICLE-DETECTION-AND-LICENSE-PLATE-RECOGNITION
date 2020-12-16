1. put the videofile (jo tere pas pehe se hoga) in vsd-lpr-system/files/ as videoTest.mp4
2. **** DON'T SHARE vsd-lpr-json-key.json, private key hai database access ka
3. Webpage is also insecure, only use it to view data, dont share.


4. MAIN_FIREBASE IS CONNECTED TO FIREBASE AND STORES DATA IN FIREBASE
5. MAIN_SQLITE IS CONNECT TO THE vsd-lpr.sqlite FILE AND STORES DATA IN THAT DATABASE
6. MAIN_SACEIMAGE SHOWS THE VIDEO AND SAVES THE IMAGE OF OVERSPEEDING CAR IN overspeeding/cars/

7. any file is not connected to OWNER_DETAILS TABLE.
8. it only saves the date, time, speed, licNo, Lic Error to database.