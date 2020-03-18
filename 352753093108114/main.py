## OWL 2 Radio
## Code version 1.5 - 03/17/2020

import machine
from machine import Pin
from machine import ADC #for analog input
import network  # to check network
import time  # for sleeping and measuring time
import xbee
import uio
import uos
import gc #For Garbage Collection
from umqtt.simple import MQTTClient  # for mqtt
import urequests
import ota

gc.collect() #Collect previous garbage
# - - - - - - - - - - - Creating all instances
x = xbee.XBee()
#mqtt = MQTTClient("XBee", "broker.mqttdashboard.com")  # Create all instances up top,
mqtt = MQTTClient("XBee", "demo.owlsite.net", 1883, "owl_demo", "enroll-double-burger-script-erupt")  # Create all instances up top,
# No need to get connected first

# --- - - - - -  -Declare all other variables - - - - -  -
global versionURL
global mainURL
global configURL
global configVersionURL
global userVariables
global timeSpent
global oldVersionNumber
configFile = "config.txt"
configVersionFile = "configVersion.txt"
mainFile = "main.py"
versionFile = "version.txt"
rebootCountFile="rebootCount.txt"
otaFile = "ota.py"
otaVersionFile = "otaVersion.txt"
start = time.time()  #This will be used if the module could not connect to the network at all
normalSleepTime = 43260000  #in mS currently set for 12hr 1 minute
imei = str(x.atcmd('IM'))  # Getting the IMEI
deviceID = imei[-7:]  # Create deviceID from IMEI
versionURL = "https://raw.githubusercontent.com/circuitronics/Otatest/master/" + imei + "/version.txt"
mainURL = "https://raw.githubusercontent.com/circuitronics/Otatest/master/" + imei + "/main.py"
configURL = "https://raw.githubusercontent.com/circuitronics/Otatest/master/" + imei + "/config.txt"
configVersionURL = "https://raw.githubusercontent.com/circuitronics/Otatest/master/" + imei + "/configVersion.txt"
otaURL = "https://raw.githubusercontent.com/circuitronics/Otatest/master/" + imei + "/ota.py"
otaVersionURL = "https://raw.githubusercontent.com/circuitronics/Otatest/master/" + imei + "/otaVersion.txt"

# - - - - - - - - - - Declaring all pins - - - - - - - -  -
turnOnAllLEDs = Pin("D7", Pin.OUT, value=0)  # This is switch for all LEDS. Starting with turned OFF
networkStatusLED = Pin("D10", Pin.OUT, value=0)  # pin 6=D10 = BLUE LED # Start with turned OFF
errorMsgLED=Pin("D9", Pin.OUT, value=0) #pin 13=D9= Red LED #Start with turned off
analogInputSwitch = Pin("D6", Pin.OUT, value=0)  # pin 16=D6 . Activates the Analog inputs. Start with turned OFF
chargePumpSwitch = Pin("D4", Pin.OUT, value=0)  # Pin 11=D4. Activates the charge booster for sensor. Starts with OFF

time.sleep(20)
print("Software Version: 1.5")
print("IMEI: ", imei)
print("Device ID: ", deviceID)
print("Disabling Airplane Mode\n")
x.atcmd('AM', 0)  # Deactivating airplane mode at first
time.sleep(2)  # Just a safety feature to prevent boot loop

# - - - - - - - Define all functions - - - - - -

# added to allow padding of strings
def zfill(s, width):
	return '{:0>{w}}'.format(s, w=width)

#  Connects to internet and returns RSSI
def isitconnected():
	global timeSpent
	timeSpent=0
	print("\n\n Checking if connected or not")
	for connecttry in range(300):
		time.sleep(2)
		timeSpent += 2
		if x.atcmd('AI') == 0:
			networkStatusLED.value(1)  # 0 means OFF
			print("\n\nI am connected.....Check LED :-)\n")
			rssi = x.atcmd('DB')
			print("Node Status= ", x.atcmd('AI'), ",RSSI= ", x.atcmd('DB'),",CI= ",x.atcmd('CI'))
			#print("Current RSSI= ", rssi)
			print("Time spent here =", timeSpent)
			return rssi

		else:
			if connecttry < 299:
				print("\nConnect try #", connecttry, ",Status= ", x.atcmd('AI'), ",RSSI= ", x.atcmd('DB'),"CI= ",x.atcmd('CI'))
				if x.atcmd('AI') == 37:
					print("- - - - - Cellular network registration denied- - - - - ")
				elif x.atcmd('AI') == 42:
					print("- - - - - Airplane mode- - - - - ")
				elif x.atcmd('AI') == 35:
					print("- - - - - Connecting to the Internet- - - - - ")
				elif x.atcmd('AI') == 255:
					print("- - - - - Initializing...- - - - - ")
				elif x.atcmd('AI') == 34:
					print("- - - - - Registering to cellular network- - - - - ")
				elif x.atcmd('AI') == 44:
					print("- - - - - Cellular component is in PSM- - - - - ")
				continue

			else:
				RedLEDErrorMsg(4) #Could not connect to network
	# Do what you need to do after trying to get connected with the network.
				rebootProcedure()
