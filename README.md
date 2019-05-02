# SiNRI - Simple Neural Response Interpreter

SiNRI is a project that works towards creating a minimalistic system
that interfaces with in-vitro neural chambers to interpret responses
to external stimuli. The project consists of several software
components, required to take external sensory input, forward it to the
chamber as stimuli, and then interpret the inner workings of the
network to decide whether to act or not.

## Getting an MEA recording

To use the SiNRI system, its is necessary to have available either a
remote MEAME server that can supply live data, or HDF5-files that
contain previous recordings. A recording is available at
http://folk.ntnu.no/thomaav/meame/. Simply download the 1.h5-file, and
put it into the mea_data directory located in the root of the project.

