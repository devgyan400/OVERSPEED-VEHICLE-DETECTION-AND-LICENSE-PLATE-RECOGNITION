from twilio.rest import Client

#--------------------------------------------------------------------

#this function will be completed and added later
def sendSMS():
    # Your Account Sid and Auth Token from twilio.com/console
    # DANGER! This is insecure. See http://twil.io/secure
    account_sid = 'AC1cde836515a1799f790785c12fa30b12'
    auth_token = 'f2045bad8b6f1f70f54a5e39cfdd3666'
    client = Client(account_sid, auth_token)

    message = client.messages \
                    .create(
                         body="Your text here",
                         from_='+12056274864',#ANURAG GUPTA's twilio phone number
                         to='+91'+str("ENTER RECIEVER CONTACT NUMBER")
                     )

    return message.sid
