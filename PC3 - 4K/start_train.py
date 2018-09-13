### TTL TRAIN PULSE CODE
### This code is meant for PC3, the Raspberry Pi that will be reading in
### the TTL train pulse from the NI board.
### Andy Thai - andy.thai9@gmail.com

# Import required libraries
import RPi.GPIO as GPIO			# Raspberry Pi specific library to read from the GPIO pins
from datetime import datetime
import time
import os
import sys
import csv

# Main method, runs everything here
def main():

	# ############# #
	#	GPIO SETUP	#
	# ############# #
	
	# GPIO pin settings
	# Here we set up the GPIOb board to be read from.
	GPIO.setmode(GPIO.BCM)

	# This is the pin the TTL train will be coming into: GPIO 26, #37 on the chart
	pin_TRAIN = 26	

	# Setup the train pin to be used as input.
	print('Setting up pin...')
	print('TTL TRAIN pin: \t' + str(pin_TRAIN))
	GPIO.setup(pin_TRAIN, GPIO.IN)

	# ######################### #
	#	DATA FILEPATH SETUP		#
	# ######################### #

	# Set up list to store timestamp variables
	timestamps = []

	# Here we get the filepath of the code (default is in the Raspberry Pi's desktop)
	# and save the data recordings to where the Python code is, within a folder named
	# train_recordings.
	cwd = os.path.realpath(__file__)
	cwd = cwd.replace("start_train.py", "train_recordings/")

	# Here we get the starting timestamp. This is used to name the data file.
	# We get rid of colons since filenames can't have colons in them.
	starting_timestamp = str(datetime.now())
	starting_timestamp = starting_timestamp.replace(":", "_")
	starting_timestamp = starting_timestamp.replace(".", "_")

	# Print out the name of the to-be-saved data file path.
	cwd = cwd + starting_timestamp + ".csv"
	print('\nData save path: ' + cwd)

	# ######################### #
	#	WAIT FOR TRAIN PULSE	#
	# ######################### #

	# Wait for initial pulse before starting.
	# We don't start until we get an initial pulse from the board
	# indicating that the process has started.
	WAIT_FOR_PULSE = True

	# The pulse input read in is binary, it will either be 0 or 1 depending
	# on the train / frames. 
	pulse = 0

	# We wait for the first 1 indicating that the TTL train has started.
	while WAIT_FOR_PULSE:
		pulse = GPIO.input(pin_TRAIN)

		# Start recording once signal is received and save the data to timestamps
		if pulse is not 0:
			WAIT_FOR_PULSE = False
			timestamps.append([str(datetime.now()), pulse])

			# Print out the pulse value. This is SOLELY for debug purposes. Once we are finished
			# testing out the code, remove or comment out this print line. 
			# Print statements will slow the system down.
			print(pulse)

	print('\nRecording train TTL started! Press CTRL + C ONCE and only ONCE at any time to stop recording.\n')

	# ######################### #
	#	READING TRAIN PULSE		#
	# ######################### #

	# Continue reading and recording the TTL train pulses until interrupted with CTRL + C.
	# Very important that you only press Ctrl + C once or data may be lost.
	try:
		while True:
			pulse = GPIO.input(pin_TRAIN)
			timestamps.append([str(datetime.now()), pulse])
			
			# Print out the pulse value. This is SOLELY for debug purposes. Once we are finished
			# testing out the code, remove or comment out this print line. 
			# Print statements will slow the system down.
			print(pulse)

	except KeyboardInterrupt:
		pass

	# ################################# #
	#	CLEANUP AND SAVING CSV DATA		#
	# &&&&&&&&######################### #	

	# Clean up the pins so none of them are reading in the board after the program has concluded.
	GPIO.cleanup()

	# Save data to csv file in train_recordings folder
	with open(cwd, 'wb') as csvfile:
		writer = csv.writer(csvfile, delimiter=',')
		writer.writerow(['Timestamp', 'Value'])
		for i in range(len(timestamps)):
			writer.writerow([timestamps[i][0], timestamps[i][1]])
	csvfile.close()

	print('\nCONCLUDE PROGRAM')
	return

# Main method, runs the entire thing.
if __name__ == "__main__":
	main()
