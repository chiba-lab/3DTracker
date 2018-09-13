### STATE CLASS CODE
### This code serves as a class for the IMU data handling.
### These essentially function as a sort of container for all
### the data the IMUs will be reading in. 
### Andy Thai - andy.thai9@gmail.com

# Import required libraries
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
import datetime

# State class that collects data from device. One State corresponds to one IMU device.
class State:
	# Initialize default settings for the State object
	def __init__(self, device):

		# Device ID
		self.device = device

		# Sample count
		# This is how many samples of data the IMU sensors have reaed in for
		# a specific type of measurement.
		self.samples_accel = 0
		self.samples_gyro = 0
		self.samples_mag = 0

		# Data streaming callback
		# This is a function that will continuously stream in data
		# from the IMUs.
		self.callback_accel = FnVoid_DataP(self.data_handler_accel)
		self.callback_gyro = FnVoid_DataP(self.data_handler_gyro)
		self.callback_mag = FnVoid_DataP(self.data_handler_mag)

		# Collected data
		# These are the lists storing the data read in by the IMU sensors.
		self.accel_data = []
		self.gyro_data = []
		self.mag_data = []

	# ################# #
	#	ACCELEROMETER	#
	# ################# #
		
	# Accelerometer
	def data_handler_accel(self, data):

		# Get the timestamps and device information
		timestamp = str(datetime.datetime.now())
		device_id = self.device.address
		
		# Parse in the data and convert it to a usable format
		xyz = parse_value(data)
		xyz = str(xyz)
		xyz = xyz.translate(None, "xyz:{}")
		x, y, z = xyz.split(',')
		x = float(x)
		y = float(y)
		z = float(z)

		# Add to the State data list and increment the count
		vec = (device_id, timestamp, x, y, z)
		self.accel_data.append(vec)
		self.samples_accel += 1

	# ############# #
	#	GYROSCOPE	#
	# ############# #
		
	# Gyroscope
	def data_handler_gyro(self, data):

		# Get the timestamps and device information
		timestamp = str(datetime.datetime.now())
		device_id = self.device.address
		
		# Parse in the data and convert it to a usable format
		xyz = parse_value(data)
		xyz = str(xyz)
		xyz = xyz.translate(None, "xyz:{}")
		x, y, z = xyz.split(',')
		x = float(x)
		y = float(y)
		z = float(z)
		
		# Add to the State data list and increment the count
		vec = (device_id, timestamp, x, y, z)
		self.gyro_data.append(vec)
		self.samples_gyro += 1

	# ############# #
	#	MAGNOMETER	#
	# ############# #		
		
	# Magnometer
	def data_handler_mag(self, data):

		# Get the timestamps and device information
		timestamp = str(datetime.datetime.now())
		device_id = self.device.address
		
		# Parse in the data and convert it to a usable format
		xyz = parse_value(data)
		xyz = str(xyz)
		xyz = xyz.translate(None, "xyz:{}")
		x, y, z = xyz.split(',')
		x = float(x)
		y = float(y)
		z = float(z)

		# Add to the State data list and increment the count
		vec = (device_id, timestamp, x, y, z)
		self.mag_data.append(vec)
		self.samples_mag += 1
