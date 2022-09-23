from webuntis import webuntis
from decouple import config

# Create WebUntis API Wrapper Object
username = config('USERNAME')
password = config('PASSWORD')
client = webuntis.Webuntis(username, password, "erato", "HH-Schule-Karlsruhe", "14163")

# Connect Client to Webuntis Server
await client.login()

#############################################################
#                                                           #
# Call all your functions in here between login and logout  #
#                                                           #
#############################################################

# In this example we print out all teachers of a student
print(await client.getteachers())

# Disconnect Client from Webuntis Server
await client.logout()
