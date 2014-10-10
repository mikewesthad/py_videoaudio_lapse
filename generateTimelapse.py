"""
	Requires ffmpeg, ffprobe and sox

	Slopppppy! This needs some serious cleanup.
"""

import math
import shutil
import subprocess
import os
import re

movieName = "VeggieRoll.mp4"
desiredDuration = 60

inputFile = os.path.join("RawClips", movieName)
movieBaseName = movieName.split(".")[0]
movieExtension = movieName.split(".")[1]

# Get movie duration
cmd = "ffprobe -i {0}".format(inputFile)
output = subprocess.check_output(cmd, stderr=subprocess.STDOUT) # ffprobe outputs the info into sterr
# Re taken from https://www.google.com/webhp?sourceid=chrome-instant&ion=1&espv=2&es_th=1&ie=UTF-8#q=python+ffmpeg+get+duration+re
matches = re.search(r"Duration:\s{1}(?P<hours>\d+?):(?P<minutes>\d+?):(?P<seconds>\d+\.\d+?),", output, re.DOTALL).groupdict()
duration = (float(matches['hours']) * 60 * 60) + (float(matches['minutes']) * 60) + float(matches['seconds'])

# Calculate the ratio needed to timelapse
durationRatio = desiredDuration / duration

# Rip timelapsed video
cmd = "ffmpeg -i {0} -filter:v \"setpts={1}*PTS\" -an videolapse.mp4".format(inputFile, durationRatio)
subprocess.call(cmd)

# Rip audio track
# 	Converting to wav since that's what sox can handle
# 	Hard coding audio format options using:
#	http://peppoj.net/2010/09/how-to-extract-audio-from-video-using-ffmpeg/
cmd = "ffmpeg -i {0} -vn -ac 2 -ar 48000 -ab 320k -f wav rippedAudio.wav".format(inputFile)
subprocess.call(cmd)

# Set up some variables for audiolapsing
soundFilePath = "rippedAudio.wav" 
sampleDuration = 0.1
samples = int(desiredDuration / sampleDuration)
timeBetweenSamples = duration / samples

# Create a directory for the audio samples
if not(os.path.exists("./Samples/")): os.mkdir("Samples")

# Generate the samples
for i in range(samples):
	startTime = i * timeBetweenSamples
	tmpFileName = "samples/sample{0}.wav".format(i)
	command = "sox {0} {1} trim {2} {3}".format(soundFilePath, 
												tmpFileName,
												startTime, 
												sampleDuration)
	subprocess.call(command) # Command doesn't seem to work using list format...

# Mix all the samples together
# 	sox bug where it can't open up more than some number of files...
# 	so mix the files together in chunks of 300!
chunkSize = 300.0
chunks = int(math.ceil(samples/chunkSize))
for chunkIndex in range(chunks):
	startFile = int(chunkIndex * chunkSize)
	endFile = int(min(samples, startFile+chunkSize))
	command = "sox "
	for fileIndex in range(startFile, endFile): 
		command += "samples/sample{0}.wav ".format(fileIndex)
	command += "samples/chunk{0}.wav".format(chunkIndex)
	subprocess.call(command)
command = "sox "
for chunkIndex in range(chunks):
	command += "samples/chunk{0}.wav ".format(chunkIndex)
command += "audiolapse.wav".format(chunkIndex)
subprocess.call(command)

# Create a directory for the timelapsed video+audio
if not(os.path.exists("./Timelapse/")): os.mkdir("Timelapse")

# Combine the audiolapse and videolapse!
outputFile = os.path.join("Timelapse", movieBaseName+"Timelapse")
command = "ffmpeg -i videolapse.mp4 -i audiolapse.wav -c:v copy -c:a aac -strict experimental {0}.mp4".format(outputFile)
subprocess.call(command)

# Cleanup!!
os.remove("videolapse.mp4")
os.remove("rippedAudio.wav")
os.remove("audiolapse.wav")
shutil.rmtree('./Samples') 