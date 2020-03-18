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

#  Config file download. Deletes config first, then downloads new one.
def downloadConfigFile():
	try:  # At first check if previous config file exists
		#log = uio.open(configFile)
		#log.close()
		uos.remove(configFile)  ##If it does, then delete it
	except OSError:
		# Do nothing, the file does not exist.
		pass

	f = urequests.get(configURL)
	print("\nTrying to get ", configURL, "\n\n")

	print(f.content)
	with uio.open(configFile, mode="w") as log:
		ab = log.write(f.content)
		log.close()
	f.close()

'''This will sort the config.txt file everytime it runs ( Except may be the first time)
It will return a list, From the main code you have to assign variables
 to each elements of this list'''


def sortConfigFile():
	global userVariables
	userVariables = []
	a = ""
	try:
		with uio.open(configFile) as log:
			for i in range(1):  # We know the number of lines
				line = log.readline()
				a = line.split("=")
				a[1] = a[1].replace("\r", "")
				a[1] = a[1].replace("\n", "")  # Remove \n from the 2nd variable
				print("a= ", a)
				userVariables.append(a)
				if not line:
					break
		log.close()
	#except (OSError, IndexError, IOError) as e: #If we experience more errors during reading the file, then we can add them inside the bracket.
	except:
		RedLEDErrorMsg(6) #Could not read the config file
		print ("\nCould not read the configuration file")
		print ("Applying the backup config settings")
		#The following line is your backup config settings
		userVariables.extend([['wakeUpFrequency', '43200000']])
	print("Printing variables: ", userVariables)


'''This will check if any new OTA update is available or not
- If there is one available, it will delete the old one
- note down the current firmware number in the versionFile
- Download and compile the new main file by calling downloadMainFile()'''


def checkIfNewMainAvailable():
	try:
		f = urequests.get(versionURL)  # reading from the internet
		print("main1")
		#print(f)
		currentVersionNumber = int(f.content)
		print("Current Firmware Version= ", currentVersionNumber)
		# Reading from the file inside the module
		with uio.open(versionFile) as log:
			oldVersionNumber = int(log.readline())
			print("main2")
			log.close()
		print("Device Firmware Version= ", oldVersionNumber)
		if oldVersionNumber < currentVersionNumber:
			print("We need new Firmware")
			downloadMainFile()  # Calling the downloadMainFile function to do its magic.
			uos.remove(versionFile)
			with uio.open(versionFile, mode="w") as log2:  # Noting down the new Firmware Version Number
				ab = log2.write(f.content)  # Can not use variable in place of f.content
				print("main3")
				log2.close()
			firmwareReboot()
		else:
			print("The current Firmware is the latest one")
		f.close()
	except:
		RedLEDErrorMsg(4) #Could not connect to network
		print ("Had problems connecting to the internet, Skipping OTA")

''' Gets called by checkIfNewMainAvailable
- It downloads the main.mpy file
- Compile the main.py file on any xbee3 module using
	import uos
	uos.compile('main.py').
	Then put that file on the server.
	As the latest mpy-cross compiled binary is not compatible with the xbee3 module.
	Need to find how to install the older version of mpy-cross

- Then it reboots the module, so that the new main.mpy file can be run at boot'''


def downloadMainFile():
	try:  # Deleting previous main
		log = uio.open(mainFile)  # May be we do not need this and the next line, Have to test
		log.close()
		print("Before Main remove")
		uos.remove(mainFile)  ##If it does, then delete it
		print("After main remove")
	except OSError:
		# Do nothing, the file does not exist.
		pass

	g = urequests.get(mainURL)
	print("\nTrying to get ", mainURL, "\n\n")
	print("before printing content")
	print(g.content)
	print("After printing Content")
	print("before opening main2")
	with uio.open("main2.py", mode="w") as log3:  # Binary write for binary file
		print("before sleep")
		time.sleep(0.01)
		print("Before writing content")
		ab = log3.write(g.content)  # Writing new main.py file
		print("before log close")
		log3.close()
	print("before g close")
	g.close()
	print("Downloaded firmware complete... Now compiling")
	time.sleep(0.1)
	uos.replace("main2.py", "main.py")
	#machine.soft_reset()  # Just rebooting


''''Gets raw voltage (out of 2.5v), and sensor input voltage (out of 5V) and sends them'''


def getSensorValue():
	print("\n\n- - - - Getting sensor readings- - - - ")
	adc0 = ADC("D0")  # d0 is pin #20
	adc0_value = adc0.read()
	adc0_voltage = (adc0_value * 2.5) / 4095
	adc0_voltage = round(adc0_voltage,2)  # round reading to 2 decimals
	print("Sensor Reading Voltage= ", adc0_voltage)

	print("\n\n- - - - Getting sensor Input voltage- - - - ")
	adc1 = ADC("D2")  # d2 is pin #18
	adc1_value = adc1.read()
	adc1_voltage = (adc1_value * 2.5) / 4095  # Not using reference to save on memory use
	adc1_voltage = round(adc1_voltage,2)
	print("Sensor Input Voltage = ", adc1_voltage)

	sensorValue = ((5 * adc0_voltage) / adc1_voltage)  # To scale it up to 5V
	sensorValue = str(sensorValue).replace('.', '')
	sensorValue = zfill(sensorValue, 3)
	print("True Voltage= ", sensorValue)
	return sensorValue

# This returns the battery voltage - It assumes battery is connected at pin #19
def getBatteryVoltage():
		print("\n\n- - - -Getting Battery Voltage- - - -")
		time.sleep(0.5)  # added half second sleep in between just for safety
		adc2 = ADC("D1")  # D1 is pin #19
		adc2_value = adc2.read()
		adc2_voltage = (adc2_value * 2.5) / 4095
		adc2_voltage = round(adc2_voltage,2) #Rounding up to two decimal points, change if necessary
		adc2_voltage = str(adc2_voltage).replace('.', '')
		adc2_voltage = zfill(adc2_voltage, 3)
		print("Battery Voltage = ", adc2_voltage)
		return adc2_voltage

'''This sends the payload string to the server, under the supplied topic
- It also makes sure that the module is connected to the internet
- If it is not then it will try again and again.
- Using while loop because if isconnected() did not give me any error then this should work
- After the module is connected then it will connect() to the MQTT server and send the value
'''

def mqttConnectAndSend(topic, payload):
	global timeSpent
	for i in range(20): #You can have network issues at this level too. So try connecting first.
		time.sleep(0.5)
		timeSpent += 0.5
		if x.atcmd('AI') == 0: #Connected to the internet
			try:
				confirm = mqtt.connect()
				if confirm == 0:  # If everything is fine. Connected to the server.
					print("Connected to the mqtt server, Now sending the string")
					print("Time spent here =", timeSpent)
					mqtt.publish(topic, str(payload))
					break
				else: #Not connected to the server
					continue
			except OSError:  # This is to handle --OSError: [Errno 7006] ENXIO--This is a DNS Lookup Failure
				print("Got OSError: [Errno 7006] ENXIO- DNS Lookup failure, but avoided it")
				RedLEDErrorMsg(2)
				continue
			except IndexError: # If the bytes get mismatched
				print("Got IndexError, check data sent")
				rebootProcedure()
				continue
		else: #Not connected to the Internet
			RedLEDErrorMsg(2) #Could not connect to server
			if i < 19: #Trying for 19 times
				print("connect try#",i," Status= ", x.atcmd('AI'), " ,RSSI= ", x.atcmd('DB'))
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
			else: #After trying for 19 times
				RedLEDErrorMsg(4) #Could not connect to network
				rebootProcedure()

	try:
		mqtt.disconnect()  # If you are connecting, you have to disconnect as well
		print("Disconnected from the MQTT server")
	except OSError:  # This is to handle --OSError: [Errno 7107] ENOTCONN
		print("Got OSError: [Errno 7107] ENOTCONN, while disconnecting from the server but avoided it")
		pass #It is kind of OK if you do not disconnect.

def MainFunction():
	global turnOnAllLEDs
	global networkStatusLED
	global analogInputSwitch
	global chargePumpSwitch
	global normalSleepTime
	global start
	global oldVersionNumber
	gc.collect()  # Collect previous garbage
	x.atcmd('AM', 0)  # Deactivating airplane mode at first

	if x.wake_reason() is xbee.PIN_WAKE: #If woke up by Pin-Disturb then switch ON all the LEDs
		turnOnAllLEDs = Pin("D7", Pin.OUT, value=1)  # This is switch for all LEDS.
	else:  # For the first time or complete sleep
		pass #For complete sleep, Do not turn on any LEDs
	with x.wake_lock:
		total = []
		rssi = isitconnected()  # Make sure the module is connected at first
		paddedRSSI = zfill(rssi, 3)
		start=time.time() #as the module is connected, it will give a correct time now
		# - - - - - -  Downloading the config file and parsing it - - - - - - -#
		checkIfNewConfigAvailable()
		checkIfNewMainAvailable()
		## checkIfNewOTAAvailable()
		ota.otaFunction()
		# sortConfigFile() would have returned userVariables list at this point,
		# you can put them into whatever variables you need
		normalSleepTime = userVariables[0][1]
		#normalSleepTime = 43200000
		print("\n\nNormal Sleep Time =", normalSleepTime, " Milliseconds")
		# - - - - - - - - - - - - Now get sensor values -  - - - - - - -
		analogInputSwitch = Pin("D6", Pin.OUT, value=1)  # Activate the analog Inputs
		chargePumpSwitch = Pin("D4", Pin.OUT, value=1)  # activate the charge boost
		sensorReading = getSensorValue()
		chargePumpSwitch = Pin("D4", Pin.OUT, value=0)  # Switch OFF the charge boost
		batteryVoltage = getBatteryVoltage()
		analogInputSwitch = Pin("D6", Pin.OUT, value=0)  # Switch OFF the Analog input
		#- - - - - - - End of sensor values - - - - -
		temperature = round((int(x.atcmd('TP'))*1.8+32),2) #Converting it to Farenheit, Rounding it up to 2 decimal points
		for j in range(5):
			time.sleep(0.1)
			currentTime = time.localtime()
		hourMinSeconds = str(currentTime[3]) + ":" + str(currentTime[4]) + ":" + str(currentTime[5])
		print("Current Time", hourMinSeconds)
		compressedString = deviceID + sensorReading + batteryVoltage + paddedRSSI + zfill(str(oldVersionNumber),3)
		total.extend([compressedString])
		#total.extend([deviceID, sensorReading, batteryVoltage, paddedRSSI]) #Add whatever you want to send here
		print(total)
		print("RSSI value is = ", paddedRSSI)
		print("Sensor value is = ", sensorReading)
		print("Battery Voltage = ", batteryVoltage)
		stringTotal = str(total)
		mqttConnectAndSend(deviceID, stringTotal)
		print("Time spent at the end of MainFunction =", timeSpent)
		networkStatusLED.value(0)  # Turn OFF Everything
		turnOnAllLEDs.value(0)  # 0 means OFF

while True:
	imei = str(x.atcmd('IM'))  # Getting the IMEI
	deviceID = imei[-7:]  # Create deviceID from IMEI

	MainFunction()
	deepSleepProcedure()
