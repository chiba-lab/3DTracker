### IMU SYSTEM CLASS CODE
### This code serves as a class for the IMU system specifications.
### This class is representative of the entire IMU system inside
### a single object which will be used in start.py
### Andy Thai - andy.thai9@gmail.com

# Import needed libraries
from State import State		# State class
from time import sleep
import sys
import csv
import os
import datetime

# Mbientlab metawear library, install from GitHub
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *

# IMU system class that stores the IMU system functions
class IMU_system:
	def __init__(self, MAC_addresses):
	
		# Container of all the States
		self.states = []
		
		# MAC addresses of the IMUs
		self.addresses = MAC_addresses
		
		# Saved filename of output data file
		self.filename = str(datetime.datetime.now()).replace(':', '_').replace('.', '_') + '.csv'

	# ############# #
	#	CONNECT		#
	# ############# #
		
	# Get all of the input MAC Addresses and put them in states
	def connect(self):
		try:
			if sys.version_info[0] == 2:
				range = xrange
				
			# Start trying to connect to all of the IMU boards
			# as saved in the MAC addresses list
			print('Connecting...')
			for i in range(len(self.addresses)):
				d = MetaWear(self.addresses[i])
				d.connect()
				print("Connected to " + d.address)
				self.states.append(State(d))
			return True	# If all IMUs connect successfully
		except RuntimeError:
			return False	# If any IMUs fail to connect

	# ################# #
	#	SETUP DEVICES	#
	# ################# #

	# Setup for every MAC address s in states
	def setup(self):
		# s represents a device's MAC address 
		for s in self.states:

			# Device configuration
			print("Configuring device...")
			
			# Not sure what these parameters are for, but they're synchronized with the rest of the settings.
			libmetawear.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)

			# Acceleration
			libmetawear.mbl_mw_acc_set_odr(s.device.board, 25.0)				# 25 Hz data collection rate
			libmetawear.mbl_mw_acc_set_range(s.device.board, 16.0)				# Unsure
			libmetawear.mbl_mw_acc_write_acceleration_config(s.device.board)	# Save to the board's configuration
			signal_acceleration = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
			libmetawear.mbl_mw_datasignal_subscribe(signal_acceleration, s.callback_accel)
			libmetawear.mbl_mw_acc_enable_acceleration_sampling(s.device.board)

			# Gyrometer
			libmetawear.mbl_mw_gyro_bmi160_set_odr(s.device.board, 6) 			# 6 is index for 25 Hz
			libmetawear.mbl_mw_gyro_bmi160_write_config(s.device.board)
			signal_gyro = libmetawear.mbl_mw_gyro_bmi160_get_rotation_data_signal(s.device.board)
			libmetawear.mbl_mw_datasignal_subscribe(signal_gyro, s.callback_gyro)
			libmetawear.mbl_mw_gyro_bmi160_enable_rotation_sampling(s.device.board)

			# Magnometer
			libmetawear.mbl_mw_mag_bmm150_configure(s.device.board, 1, 1, 6)	# 6 is index for 25 Hz
			signal_mag = libmetawear.mbl_mw_mag_bmm150_get_b_field_data_signal(s.device.board)
			libmetawear.mbl_mw_datasignal_subscribe(signal_mag, s.callback_mag)

			# Run LED - Stays green until IMUs / system starts with a pulse
			pattern = LedPattern(repeat_count=Const.LED_REPEAT_INDEFINITELY)
			libmetawear.mbl_mw_led_load_preset_pattern(byref(pattern), LedPreset.SOLID)
			libmetawear.mbl_mw_led_write_pattern(s.device.board, byref(pattern), LedColor.GREEN)
			libmetawear.mbl_mw_led_play(s.device.board)
		return

	# ######################### #
	#	START DATA COLLECTION	#
	# ######################### #

	# Start after receiving the start TTL pulse
	def start(self):
		# Start every piece of data collection for every address
		for s in self.states:
			libmetawear.mbl_mw_acc_start(s.device.board)
			libmetawear.mbl_mw_gyro_bmi160_start(s.device.board)
			libmetawear.mbl_mw_mag_bmm150_enable_b_field_sampling(s.device.board)
			libmetawear.mbl_mw_mag_bmm150_start(s.device.board)
			libmetawear.mbl_mw_led_stop_and_clear(s.device.board)
		return

	# ######################### #
	#	STOP DATA COLLECTION	#
	# ######################### #

	# Stop collecting data and disconnect boards
	def stop(self):
		for s in self.states:

			# Disable acceleration
			libmetawear.mbl_mw_acc_stop(s.device.board)
			libmetawear.mbl_mw_acc_disable_acceleration_sampling(s.device.board)
			signal_acceleration = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
			libmetawear.mbl_mw_datasignal_unsubscribe(signal_acceleration)

			# Disable gyro
			libmetawear.mbl_mw_gyro_bmi160_stop(s.device.board)
			libmetawear.mbl_mw_gyro_bmi160_disable_rotation_sampling(s.device.board)
			signal_gyro = libmetawear.mbl_mw_gyro_bmi160_get_rotation_data_signal(s.device.board)
			libmetawear.mbl_mw_datasignal_unsubscribe(signal_gyro)

			# Disable magnometer
			libmetawear.mbl_mw_mag_bmm150_stop(s.device.board)
			libmetawear.mbl_mw_mag_bmm150_disable_b_field_sampling(s.device.board)

			# Disconnect board and turn off LED
			libmetawear.mbl_mw_debug_disconnect(s.device.board)
		return

	# ############# #
	#	PRINT INFO	#
	# ############# #

	# Print out sensor information post-recording
	def print_samples(self):
		# Print out total samples received per board
		print("\nTotal Samples Received")
		for s in self.states:
			print("%s Accelerometer \t-> %d samples" % (s.device.address, s.samples_accel))
			print("%s Gyro \t\t\t-> %d samples" % (s.device.address, s.samples_gyro))
			print("%s Magnometer \t\t-> %d samples" % (s.device.address, s.samples_mag))
		# Print out first 10 samples per device
		for s in self.states:
			print("\nFIRST 10 SAMPLE DATA POINTS for " + str(s.device.address))
			print_num = 10  # Print the first 10 entries
			print("\nAccelerometer:")
			i = 0
			for item in s.accel_data:
				if i < print_num:
					print(str(item[1]) + ' ' + str(item[2]) + ' ' + str(item[3]) + ' ' + str(item[4]))
					i += 1
				else:
					break
			print("\nGyroscope:")
			i = 0
			for item in s.gyro_data:
				if i < print_num:
					print(str(item[1]) + ' ' + str(item[2]) + ' ' + str(item[3]) + ' ' + str(item[4]))
					i += 1
				else:
					break
			print("\nMagnometer:")
			i = 0
			for item in s.mag_data:
				if i < print_num:
					print(str(item[1]) + ' ' + str(item[2]) + ' ' + str(item[3]) + ' ' + str(item[4]))
					i += 1
				else:
					break
			print('\nNum. of Accelerometer recordings: ' + str(s.samples_accel))
			print('Num. of Gyroscope recordings: ' + str(s.samples_gyro))
			print('Num. of Magnometer recordings: ' + str(s.samples_mag))
		return

	# ############# #
	#	SAVE CSV	#
	# ############# #

	# Save data to csv file in recordings folder
	def save(self):
		cwd = os.path.realpath(__file__)
		cwd = cwd.replace("IMU_system.pyc", "recordings/")
		cwd = cwd.replace("IMU_system.py", "recordings/")

		print('Saving to ' + cwd + self.filename + '...')
		with open(cwd + self.filename, 'wb') as csvfile:
			writer = csv.writer(csvfile, delimiter=',')
			
			# Create the first row of labels
			writer.writerow(['Device MAC', 'Data type', 'Timestamp',
								 'x', 'y', 'z'])
		
			for i in range(0, len(self.states)):
				current = self.states[i]
				# Write accelerometer data
				for j in range(0, len(current.accel_data)):
					writer.writerow([current.device.address, 'accel', current.accel_data[j][1], current.accel_data[j][2], current.accel_data[j][3], current.accel_data[j][4]])
				# Write gyroscope data
				for j in range(0, len(current.gyro_data)):
					writer.writerow([current.device.address, 'gyro', current.gyro_data[j][1], current.gyro_data[j][2], current.gyro_data[j][3], current.gyro_data[j][4]])
				# Write magnometer data
				for j in range(0, len(current.mag_data)):
					writer.writerow([current.device.address, 'mag', current.mag_data[j][1], current.mag_data[j][2], current.mag_data[j][3], current.mag_data[j][4]])
		csvfile.close()
		print('\nCONCLUDE PROGRAM')
		return
