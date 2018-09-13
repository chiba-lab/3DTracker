### START.PY
### This code takes all of the existing classes and implements
### them in running code. All of the code is initialized and run
### here to actually start the system.
### Andy Thai - andy.thai9@gmail.com

# Import required libraries
from IMU_system import IMU_system
import RPi.GPIO as GPIO
import time

# ############# #
#	MAIN METHOD	#
# ############# #

def main():

	# ################# #
	#	SETUP GPIO PINS	#
	# ################# #
	
	# GPIO pin Settings
	GPIO.setmode(GPIO.BCM)
	pin_START = 6   	# Blue, ON pin
	pin_END = 13    	# Black, OFF pin

	# ############################# #
	#	SETUP IMUS TO CONNECT TO	#
	# ############################# #
	
	# IMU settings
	# The IMU MAC addresses can be declared here.
	IMU_rat1 = 'CD:E9:3D:7E:FA:23'
	IMU_rat2 = 'F3:8A:E3:05:B2:CF'
	MAC_addresses = []

	# Push in IMU MAC addresses here
	# This basically adds the MAC addresses to the 
	# MAC addresses list so it can be iterated through and run.
	# To run the system without connecting to the IMU systems, just
	# comment this part out.
	## MAC_addresses.append(IMU_rat1)
	## MAC_addresses.append(IMU_rat2)	
	
	# OTHER SETTINGS
	STOP_TIME = 1		# Amount of seconds to send the stop pulse for (default 1 second)
	INITIAL_PULSE = False	# If True, sends low pulses to ON and OFF when starting program, before pressing ENTER

	# ######################### #
	#	START THE CONNECTIONS	#
	# ######################### #
	
	# Setup the start and end pins. Sets up the pins to be outputting signals.
	print('Setting up pins...')
	print('START pin: \t' + str(pin_START))
	print('END pin: \t' + str(pin_END))
	GPIO.setup(pin_START, GPIO.OUT)
	GPIO.setup(pin_END, GPIO.OUT)
	
	# ################# #
	#	CONNECT TO IMUS	#
	# ################# #

	# Setup the IMU systems
	print('\nSetting up IMUs...')
	print('IMU MAC addresses: ')
	print(MAC_addresses)
	IMU = IMU_system(MAC_addresses)

	# Check if all IMUs have successfully connected
	connection_success = IMU.connect()
	if not connection_success:	# Else terminate
		print('\nERROR: Not all IMUs successfully connected. Reset the IMUs and try again.')
		print('Make sure Bluetooth is enabled and you run the script using sudo.')
		GPIO.cleanup()
		
		# Stop the program and terminate.
		return
		
	# Otherwise if it's reached this point, all of the IMUs have connected.
	IMU.setup()
	
	# ######################### #
	#	INITIAL PULSE SIGNALS	#
	# ######################### #
	
	# Start low voltage signal output. This is the baseline for "off".
	if INITIAL_PULSE is True:
		GPIO.output(pin_START, GPIO.LOW)
		GPIO.output(pin_END, GPIO.LOW)

	# ################################# #
	#	RECORDING OFFICIALLY STARTED	#
	# ################################# #

	# Wait for user input
	try:
		input('\nPress ENTER to start recording.')
	# Catch any EOF parser errors to prevent premature crashing.
	except SyntaxError:
		pass

	# Very important that Ctrl + C is only pressed ONCE!
	print('\nRecording started! Press CTRL + C ONCE at any time to stop recording.\n')

	# Start the IMUs
	IMU.start()
	
	# ##################### #
	#	SEND SIGNAL LOOP	#
	# ##################### #

	# Continue until interrupted.
	try:
		while(True):
			# Send the proper signals respective to each pin, then sleep for a short moment, and repeat.
			GPIO.output(pin_END, GPIO.LOW)
			GPIO.output(pin_START, GPIO.HIGH)
			time.sleep(0.001)
			GPIO.output(pin_START, GPIO.LOW)
			time.sleep(0.001)

	# Keep doing this until Ctrl + C is pressed.
	except KeyboardInterrupt:
		pass

	# ##################### #
	#	STOP COLLECTION		#
	# ##################### #

	# Stop the IMUs once the stop Ctrl + C is received. 
	IMU.stop()

	# Stop the pulses (give a one second buffer time)
	print('\n\nRecording stopped!\n')
	start_time = time.time()
	end_time = time.time()
	while (end_time - start_time < STOP_TIME):
		end_time = time.time()
		GPIO.output(pin_START, GPIO.LOW)
		GPIO.output(pin_END, GPIO.HIGH)

	# ######################### #
	#	PRINT AND SAVE INFO		#
	# ######################### #		

	# Print out IMU information and save
	IMU.print_samples()
	IMU.save()

	# Clean up the pins
	GPIO.cleanup()

# Run the main method here.
if __name__ == "__main__":
	main()
