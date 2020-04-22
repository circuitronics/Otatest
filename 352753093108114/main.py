import time  # for sleeping and measuring time
import xbee
from OSystem import deepSleepProcedure
from OMain import MainFunction
import gc

xbee.XBee().atcmd('AM', 0)  # Deactivating airplane mode at first
time.sleep(10)  # Just a safety feature to prevent boot loop
# userVariables = []
imei = str(xbee.XBee().atcmd('IM'))  # Getting the IMEI
deviceID = imei[-7:]  # Create deviceID from IMEI

while True:
	gc.collect()
	print("mem free: ", gc.mem_free())
	imei = str(xbee.XBee().atcmd('IM'))  # Getting the IMEI
	deviceID = imei[-7:]  # Create deviceID from IMEI
	print("IMEI: ", imei)
	print("DevID: ", deviceID)
	MainFunction()
	# BreakPlease()
	deepSleepProcedure()