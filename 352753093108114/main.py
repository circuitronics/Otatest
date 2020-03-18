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


def RedLEDErrorMsg(number):
	for i in range(number):
		errorMsgLED.value(1)
		time.sleep(0.2)
		errorMsgLED.value(0)
		time.sleep(0.2)
	print("Red LED should blink")


def rebootProcedure():
	print("\nStarting Reboot")
	gc.collect()
	try:
		with uio.open(rebootCountFile) as log:
			rebootCount = int(log.readline())
			log.close()
		print("Reboot Count = ", rebootCount)
		if rebootCount == 0: #Then only reboot
			x.atcmd('AM', 1)  # Activating airplane mode, so that I can do the force reset
			print("Activating Airplane Mode.")
			uos.remove(rebootCountFile) #addition on 1-6-20
			with uio.open(rebootCountFile, mode="w") as log2:  # Noting down the reboot Count #changed to write (w) mode from append mode (a) on 1-6-20
				time.sleep(0.2)
				ab = log2.write("1") # Can not use variable in place of f.content. Adding one so that we know how many times we have rebooted.
				log2.close()
			time.sleep(0.2)
			x.atcmd('FR')  # Looks like I need a force reset, soft reset is not working
		else:
			print("I have rebooted enough, now I will just sleep")
			uos.remove(rebootCountFile) #addition on 1-6-20
			with uio.open(rebootCountFile, mode="w") as log2:  # Noting down the reboot Count #changed to write (w) mode from append mode (a) on 1-6-20
				time.sleep(0.2)
				ab = log2.write("0")  #Making the reboot count back to 0, so that the next time it needs reboot it will be able to.
			deepSleepProcedure() #Then call the Deep-Sleep function

	except AssertionError as msg: #addition on 1-6-20
		print("Assertion error happened but will sleep anyway")
		print(msg)
		deepSleepProcedure()

	except:
		print("Some error happened. Sleeping anyway")
		deepSleepProcedure()

def firmwareReboot():
	print("\nRebooting for firmware upgrade")
	gc.collect()
	try:
		x.atcmd('AM', 1)  # Activating airplane mode, so that I can do the force reset
		print("Activating Airplane Mode.")
		time.sleep(1)
		print("Rebooting.")
		x.atcmd('FR')  # Looks like I need a force reset, soft reset is not working

	except AssertionError as msg: #addition on 1-6-20
		print("Assertion error happened but will sleep anyway")
		print(msg)
		deepSleepProcedure()

	except:
		print("Some error happened. Sleeping anyway")
		deepSleepProcedure()

def deepSleepProcedure():
	global sleep_ms
	global start
	global timeSpent
	x.atcmd('AM', 1)  # Activating airplane mode, so that we can sleep peacefully
	gc.collect()  # Collect previous garbage
	end = time.time()
	print("Start time= ", start,"End Time= ", end)
	timeSpent += (end - start) #in Seconds
	print("Time spent= ", timeSpent , " Seconds")
	timeSpent_MS = timeSpent*1000
	if x.wake_reason() is xbee.PIN_WAKE:
		reason = "Pin disturb" #Can send this to the server if you want to know if the sleep was disturbed or not.
		print("\nWoke up due to pin.")
		deepSleepTime = int(normalSleepTime) - int(sleep_ms) - int(timeSpent_MS) #Adjust for the disturbed sleep time and time spent doing things.
	else: #For the first time or complete sleep
		deepSleepTime = int(normalSleepTime)-int(timeSpent_MS) #Adjust for only time spent doing things.
		reason = "Complete Sleep"

	print("The reason I woke up = ", reason)
	print("Deep-Sleep Time = ", deepSleepTime)
	print("Sleeping for ", float(deepSleepTime / 60000), " minutes.")
	if deepSleepTime < 1:
		deepSleepTime = normalSleepTime
		print("\nDeepSleep was negative. Reset to normal sleep time.")
	try:
		sleep_ms = x.sleep_now(deepSleepTime, True)
	except:
		print("\nDeep-sleep was not calculated properly, Using the default Deep-Sleep timer")
		print("Sleeping for ", float(int(normalSleepTime)/60000), " minutes.")
		sleep_ms = x.sleep_now(int(normalSleepTime), True)
	# - - - - - - - - - - - - - - -  This shows up after waking up - - - - - - -
	print("\n\nSystem wake up. Slept for %u Milliseconds" % sleep_ms)

	print("The reason I woke up , x.wake_reason= ", x.wake_reason())


	'''

	1.Need to create the configVersionURL before this is called.

	2. Need to store the configVersionFile in the module. As it compares the integer number
	stored in this file with the integer number stored from the configVersionURL

	3. For the first time, keeping configFile onboard is optional. As the version would be 0
	So, it will download a new config file anyway

	4. If we need new config then it will call the downloadConfigFile() function'''

'''def checkIfNewOTAAvailable():
	global oldVersionNumber
	try:
		with uio.open(otaVersionFile) as log:
			oldVersionNumber = int(log.readline())
			log.close()
		print("Device OTA Version= ", oldVersionNumber)
		f = urequests.get(otaVersionURL)  # reading from the internet
		currentVersionNumber = int(f.content)
		print("Current OTA Version on the server = ", currentVersionNumber)
		print("IMEI: ", imei)
		# Reading from the file
		if oldVersionNumber < currentVersionNumber:
			print("We need new OTA")
			uos.remove(otaVersionFile)
			downloadOTAFile()  # Downloading ConfigFile
			time.sleep(0.1)
			with uio.open(otaVersionFile, mode="w") as log2:  # Noting down the configuration Number I just downloaded
				time.sleep(0.2)
				ab = log2.write(f.content)  # Can not use variable in place of f.content
				log2.close()
			print("Need to reboot to apply OTA")
			rebootProcedure()
		else:
			print("The current OTA is the latest one")
		f.close()
	except:
		print ("There was some problem reading OTA version from the internet")
		RedLEDErrorMsg(2)
	return oldVersionNumber

def downloadOTAFile():
	try:  # At first check if previous ota file exists
		#log = uio.open(configFile)
		#log.close()
		uos.remove(otaFile)  ##If it does, then delete it
	except OSError:
		# Do nothing, the file does not exist.
		pass

	f = urequests.get(otaURL)
	print("\nTrying to get ", otaURL, "\n\n")

	print(f.content)
	with uio.open(otaFile, mode="w") as log:
		ab = log.write(f.content)
		log.close()
	f.close()

'''

def checkIfNewConfigAvailable():
	global oldVersionNumber
	try:
		with uio.open(configVersionFile) as log:
			oldVersionNumber = int(log.readline())
			log.close()
		print("Device Config Version= ", oldVersionNumber)
		f = urequests.get(configVersionURL)  # reading from the internet
		currentVersionNumber = int(f.content)
		print("Current Config Version on the server = ", currentVersionNumber)
		print("IMEI: ", imei)
		# Reading from the file
		if oldVersionNumber < currentVersionNumber:
			print("We need new configuration")
			uos.remove(configVersionFile)
			downloadConfigFile()  # Downloading ConfigFile
			time.sleep(0.1)
			with uio.open(configVersionFile, mode="w") as log2:  # Noting down the configuration Number I just downloaded
				time.sleep(0.2)
				ab = log2.write(f.content)  # Can not use variable in place of f.content
				log2.close()
			sortConfigFile()  # Sorting the new config file
		else:
			sortConfigFile()  # Sorting the existing config file
			print("The current configuration is the latest one")
		f.close()
	except:
		print ("There was some problem reading configuration version from the internet, Sorting the existing one")
		RedLEDErrorMsg(2)
		sortConfigFile()
	return oldVersionNumber
