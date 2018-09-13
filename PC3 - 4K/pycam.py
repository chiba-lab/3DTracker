### 4K Camera Code
### This code will take in multiple BRIO cameras and record from them simultaneously. 
### Andy Thai - andy.thai9@gmail.com

# General libraries
from __future__ import print_function
import argparse
import datetime
from threading import Thread
import time

# Video / image utilities
import cv2
from imutils.video import WebcamVideoStream
from imutils.video import FPS
import imutils

# NiDAQMX libraries
# Install with pip install nidaqmx
import nidaqmx
from nidaqmx.constants import LineGrouping

# NiDAQMX Settings
DEVICE_NAME = 'Dev_3DT'									# Name of NI Lab device
ON = DEVICE_NAME + '/port1/line0'						# Port for ON pulse (1.0)
OFF = DEVICE_NAME + '/port1/line1'						# Port for OFF pulse (1.1)

## FPS COUNTER CLASS
## This is a separate class from the camera. It times the frames per second and returns an
## estimate of the average FPS through the entire video recording. 
class FPS:
	def __init__(self):
		# Store the start time, end time, and total number of frames
		# that were examined between the start and end intervals
		self._start = None
		self._end = None
		self._numFrames = 0

	def start(self):
		# Start the timer
		self._start = datetime.datetime.now()
		return self

	def stop(self):
		# Stop the timer
		self._end = datetime.datetime.now()

	def update(self):
		# Increment the total number of frames examined during the
		# start and end intervals
		self._numFrames += 1

	def elapsed(self):
		# Return the total number of seconds between the start and
		# end interval
		return (self._end - self._start).total_seconds()

	def fps(self):
		# Compute the (approximate) frames per second
		if self.elapsed() == 0:
			return 0
		else:
			return self._numFrames / self.elapsed()

## WEBCAM CLASS
## This is a class for an object that represents a single camera. 
## It requires initialization before use, and has the FPS counter integrated into it.
class WebcamVideoStream:
	def __init__(self, src=0):
		# Initialize the video camera stream
		self.stream = cv2.VideoCapture(src)
		self.stream.set(3, 4096)						# Index 3 = width (default 4096)
		self.stream.set(4, 2160)						# Index 4 = height (default 2160)
		self.stream.set(5, 30.0)						# Index 5 = camera's internal max fps
		self.resolution = (4096, 2160)					# Tuple that holds default resolution pairing

		# Output settings
		self.fps = -1									# FPS for output video
		self.video_name = ''							# Output path file (where it will be saved)
		self.fourcc = ''								# Codec to use (XVID to save space, IYUV for more FPS)
		self.out = -1									# Videowriter variable, used to actually write video data to disk

		# FPS information and synchronization initialization
		self.FPS_counter = FPS()
		self.frame_index = -1							# Frame refresh rate. This is used to keep the video recording FPS in sync. 
		self.current_frame = 0							# Current frame index
		self.num_frames = -1							# Number of seconds to record * fps

		# Read the first frame from the stream
		(self.grabbed, self.frame) = self.stream.read()

		# Initialize the variable used to indicate if the thread should be stopped
		self.stopped = False

	def start(self):
		# Start the thread to read and write frames from the video stream
		self.FPS_counter.start()
		Thread(target=self.update, args=()).start()
		Thread(target=self.write, args=()).start()
		return self

	def update(self):
		# Keep looping infinitely until the thread is stopped
		while True:
			# If the thread indicator variable is set, stop the thread
			if self.stopped:
				return

			# Otherwise, read the next frame from the stream
			(self.grabbed, self.frame) = self.stream.read()

	def write(self):
		# Keep looping infinitely until the thread is stopped
		while True:
			# If the thread indicator variable is set, stop the thread
			if self.stopped:
				return

			# Otherwise, write the next frame to the output file
			end = datetime.datetime.now()
			elaps = end - self.FPS_counter._start

			# Synchronize writing frames to standardize video length
			# This is required so the frames per second remain consistent
			# throughout video recording. Otherwise FPS will jump around and
			# mess up the length of the video.
			if elaps.total_seconds() > self.frame_index * self.current_frame:
				self.out.write(self.frame)
				self.current_frame += 1

				# Update FPS counter
				self.FPS_counter.update()

	def read(self):
		# Return the frame most recently read
		return self.frame

	def stop(self):
		# Indicate that the thread should be stopped
		self.stopped = True
		self.FPS_counter.stop()
		# Wait five seconds before terminating to allow for 
		# background processes to close down to avoid any errors.
		time.sleep(5)
		self.stream.release()
		self.out.release()

## MAIN METHOD
## We actually run the code here.
def main():

	# ######################### #
	#	ARGUMENT DEFINITIONS	#
	# ######################### #

	# ARGUMENT DEFINITION
	# Construct the argument parser and parse the arguments.
	# This is where the input arguments for this program is read in.
	# These arguments are read in through the Python command line. Otherwise,
	# if they are not specified, they will be the default values.
	ap = argparse.ArgumentParser()

	# Number of seconds to record the video for.
	# Keep -1 to keep recording indefinitely until user input terminates program.
	# -1 will put it in TTL mode, where it will wait for a pulse before starting.
	# Otherwise it will just start immediately and record for the provided amount of seconds.
	# Specifying a duration that isn't -1 is best used for benchmarking.
	# Default: -1
	ap.add_argument("-s", "--seconds", type=int, default=-1,
		help="Number of seconds to record video for (default: -1)")

	# FPS of the output video.
	# Avoid values that are too high. Otherwise the output video will 
	# not be synchronized and will be too short relative to the recording time.
	# Default: 5
	ap.add_argument("-f", "--fps", type=int, default=5,
	help="Output video file's FPS rate (default: 5)")

	# Codec used for the output video.
	# Testing between different codecs indicate that we should consider between
	# YUV (codec: IYUV) or XVID (codec: XVID). YUV will give better FPS performance
	# on this computer, but will cause output files to be huge. 
	# XVID is fairly slower, but files are relatively small and compressed.
	# Potential alternatives can also include MJPG, which is the fastest, but highly compressed
	# and will affect video quality more so than the other codecs.
	ap.add_argument("-c", "--codec", type=str, default='IYUV',
	help="Codec to use; use IYUV for better FPS, XVID for more compression, MJPG for fastest FPS but hurts quality (default: \"IYUV\")")

	# Path to save the recorded video files. 
	# Default: outputX.avi, where X is the respective camera the video was recording from. 
	ap.add_argument("-o1", "--out1", type=str, default='output1.avi',
		help="Name of the output file path for camera 1 (default: \"output1.avi\")")
	ap.add_argument("-o2", "--out2", type=str, default='output2.avi',
		help="Name of the output file path for camera 2 (default: \"output2.avi\")")
	ap.add_argument("-o3", "--out3", type=str, default='output3.avi',
		help="Name of the output file path for camera 3 (default: \"output3.avi\")")
	ap.add_argument("-o4", "--out4", type=str, default='output4.avi',
		help="Name of the output file path for camera 4 (default: \"output4.avi\")")

	# Camera indexes. This is the USB index the program will connect to in order to
	# read from the cameras.
	# Default: 0, 1, 2, 3 for cameras 1, 2, 3, and 4 respectively.
	# Highly RECOMMENDED to find out and specify the correct indices for the cameras.
	# There is a high probability that the default values are incorrect for most cases.
	ap.add_argument("-c1", "--cam1", type=int, default=0,
		help="Index value for camera 1 (default: 0)")
	ap.add_argument("-c2", "--cam2", type=int, default=1,
		help="Index value for camera 2 (default: 1)")
	ap.add_argument("-c3", "--cam3", type=int, default=2,
		help="Index value for camera 3 (default: 2)")
	ap.add_argument("-c4", "--cam4", type=int, default=3,
		help="Index value for camera 4 (default: 3)")

	# Conclude parsing the arguments.
	args = vars(ap.parse_args())

	# ##################### #
	#		PRINT INFO		#
	# ##################### #

	# PRELIMINARY INFORMATION
	# Print out the parameter information before starting the stream.
	print('[INST] Starting 4K camera program.')
	print('[INST] Make sure start.py on the rPi is already initiated and ready to start!\n')
	print('[STAT] camera 1 index: ' + str(args["cam1"]))
	print('[STAT] camera 2 index: ' + str(args["cam2"]))
	print('[STAT] camera 3 index: ' + str(args["cam3"]))
	print('[STAT] camera 4 index: ' + str(args["cam4"]))
	print('[STAT] seconds: ' + str(args["seconds"]))
	print('[STAT] fps: ' + str(args["fps"]))
	print('[STAT] codec: ' + str(args["codec"]))
	print('[STAT] output path 1: ' + str(args["out1"]))
	print('[STAT] output path 2: ' + str(args["out2"]))
	print('[STAT] output path 3: ' + str(args["out3"]))
	print('[STAT] output path 4: ' + str(args["out4"]))
	print('[STAT] NI Lab device: ' + DEVICE_NAME)
	print('[STAT] NI on port: ' + ON)
	print('[STAT] NI off port: ' + OFF)

	# ##################### #
	#	INITIALIZE CAMERAS	#
	# ##################### #
	
	# You can manually edit the codec here if needed.
	FOURCC_CODEC = cv2.VideoWriter_fourcc(*args["codec"])

	# INITIALIZE CAMERA STREAMS
	# Creates a *threaded* video stream, allow the camera sensor to warm-up,
	# and starts the FPS counter
	# Camera 1 setup
	print("\n[INFO] Initializing video camera stream 1...")
	vs1 = WebcamVideoStream(src=args["cam1"])		# Record from index 
	vs1.fps = args["fps"]							# Set FPS
	vs1.num_frames = args["seconds"] * vs1.fps		# Set total amount of frames to record
	vs1.out = cv2.VideoWriter(args["out1"], FOURCC_CODEC, vs1.fps, vs1.resolution)
	vs1.frame_index = 1 / vs1.fps

	# Camera 2 setup
	print("\n[INFO] Initializing video camera stream 2...")
	vs2 = WebcamVideoStream(src=args["cam2"])		# Record from index
	vs2.fps = args["fps"]							# Set FPS
	vs2.num_frames = args["seconds"] * vs2.fps		# Set total amount of frames to record
	vs2.out = cv2.VideoWriter(args["out2"], FOURCC_CODEC, vs2.fps, vs2.resolution)
	vs2.frame_index = 1 / vs2.fps

	# Camera 3 setup
	print("\n[INFO] Initializing video camera stream 3...")
	vs3 = WebcamVideoStream(src=args["cam3"])		# Record from index
	vs3.fps = args["fps"]							# Set FPS
	vs3.num_frames = args["seconds"] * vs3.fps		# Set total amount of frames to record
	vs3.out = cv2.VideoWriter(args["out3"], FOURCC_CODEC, vs3.fps, vs3.resolution)
	vs3.frame_index = 1 / vs3.fps

	# Camera 4 setup
	print("\n[INFO] Initializing video camera stream 4...")
	vs4 = WebcamVideoStream(src=args["cam4"])		# Record from index
	vs4.fps = args["fps"]							# Set FPS
	vs4.num_frames = args["seconds"] * vs4.fps		# Set total amount of frames to record
	vs4.out = cv2.VideoWriter(args["out4"], FOURCC_CODEC, vs4.fps, vs4.resolution)
	vs4.frame_index = 1 / vs4.fps

	# ################# #
	#	READ ON PULSES	#
	# ################# #

	# INITIALIZE NIDAQ TASK for TTL
	# At this point we keep reading for pulses from the ON port until we get a signal to actually start.
	if args["seconds"] == -1:	# If seconds is set to -1, it will be considered in TTL mode and will wait for a pulse before starting.
		# Setup a task to read from ON-port (1.0)
		task = nidaqmx.Task()
		task.di_channels.add_di_chan(ON, line_grouping=LineGrouping.CHAN_PER_LINE)  # Read from ON port (1.0)
		# Wait for pulse before starting
		print('[INFO] Waiting for TTL pulse...')
		PULSE_START = False

		# Keep reading from the port until a valid pulse is detected.
		while PULSE_START is False:
			# Read input data
			data = task.read(number_of_samples_per_channel=1)		
			# Check if ON pulse occurred, if so, start recording.
			if data[0] is True:
				PULSE_START = True
				task.close()

	# ######################### #
	#	START VIDEO STREAMS		#
	# ######################### #

	# Start the video streams
	vs1.start()
	vs2.start()
	vs3.start()
	vs4.start()

	print("\n[INFO] Recording...")

	# ######################### #
	#	WAIT FOR END CONDITION	#
	# ######################### #

	# INITIALIZE IF RECORDING BY TIME
	# This only runs if a duration for seconds is provided.
	if args["seconds"] != -1:

		# Keep recording until the time duration is reached.
		print('[DEBG] Initialize time-based recording...')
		start = datetime.datetime.now()
		end = datetime.datetime.now()
		while (end - start).total_seconds() < args["seconds"]:
			# Do nothing, wait out the time period
			end = datetime.datetime.now()

	# INITIALIZE IF RECORDING WITH TTL
	# STOP NIDAQ TASK for TTL
	# Here we keep recording from the off port, waiting for a signal to stop.
	# The cameras will keep recording until a valid off pulse is read.
	if args["seconds"] == -1:
		print('[DEBG] Initialize TTL-based recording...')
		# Keep reading in TTL pulse to know when to stop
		PULSE_STOP = False

		# Setup task to read from OFF-port (1.1)
		task = nidaqmx.Task()
		task.di_channels.add_di_chan(OFF, line_grouping=LineGrouping.CHAN_PER_LINE)

		# Keep recording until stop pulse is sent
		while PULSE_STOP is False:	

			# Read from OFF port (1.1)
			data = task.read(number_of_samples_per_channel=1)

			# Check if OFF pulse occurred, and if so, stop recording.
			if data[0] is True:
				PULSE_STOP = True
				task.close()

	# ################# #
	#	STOP RECORDING	#
	# ################# #	

	# Stop recording from all the streams.
	# All these streams must be stopped via multithreading due to the five second sleep command
	# in the stop function. Otherwise there would be a five second gap between each video file closing.
	# The five second gap is required to prevent crashes from premature closing.
	print('[INFO] Recording stopping...')
	# Create the threads
	vs1_thread = Thread(target=vs1.stop, args=())
	vs2_thread = Thread(target=vs2.stop, args=())
	vs3_thread = Thread(target=vs3.stop, args=())
	vs4_thread = Thread(target=vs4.stop, args=())
	# Start all the threads
	vs1_thread.start()
	vs2_thread.start()
	vs3_thread.start()
	vs4_thread.start()
	# Wait for all of the threads to finish
	vs1_thread.join()
	vs2_thread.join()
	vs3_thread.join()
	vs4_thread.join()
	print('[INFO] All recordings stopped!')

	# ######################### #
	#	PRINT FPS INFORMATION	#
	# ######################### #

	# Print out FPS here. 
	# It is CRUCIAL to note that the average FPS for each camera must be extremely close to the target
	# FPS, otherwise there will be timing and synchronization issues (Videos will be shorter than
	# the expected length!)
	average_fps1 = vs1.FPS_counter.fps()
	print('\nAverage FPS for camera 1: \t' + str(average_fps1))
	print('Target FPS: \t' + str(vs1.fps))
	if round(average_fps1) < vs1.fps:
		print('[WARNING]: Average output FPS for camera 1 does not closely match specified FPS!')

	average_fps2 = vs2.FPS_counter.fps()
	print('\nAverage FPS for camera 2: \t' + str(average_fps2))
	print('Target FPS: \t' + str(vs2.fps))
	if round(average_fps2) < vs2.fps:
		print('[WARNING]: Average output FPS for camera 2 does not closely match specified FPS!')

	average_fps3 = vs3.FPS_counter.fps()
	print('\nAverage FPS for camera 3: \t' + str(average_fps3))
	print('Target FPS: \t' + str(vs3.fps))
	if round(average_fps3) < vs3.fps:
		print('[WARNING]: Average output FPS for camera 3 does not closely match specified FPS!')

	average_fps4 = vs4.FPS_counter.fps()
	print('\nAverage FPS for camera 4: \t' + str(average_fps4))
	print('Target FPS: \t' + str(vs4.fps))
	if round(average_fps4) < vs4.fps:
		print('[WARNING]: Average output FPS for camera 4 does not closely match specified FPS!')

	print('\nPROGRAM CONCLUDED!')
	return

# Main method, runs the entire thing.
if __name__ == "__main__":
	main()