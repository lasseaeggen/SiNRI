# SiNRI - Simple Neural Response Interpreter

SiNRI is a project that works towards creating a minimalistic system
that interfaces with in-vitro neural chambers to interpret responses
to external stimuli. The project consists of several software
components, required to take external sensory input, forward it to the
chamber as stimuli, and then interpret the inner workings of the
network to decide whether to act or not.

SiNRI is built to work on Linux, specifically to work on a robot used
for the NTNU Cyborg project.

## Getting an MEA recording

To use the SiNRI system, it is necessary to have available either a
remote MEAME server that can supply live data, or HDF5-files that
contain previous recordings. A recording is available at
http://folk.ntnu.no/thomaav/meame/. Simply download the 1.h5-file, and
put it into the mea_data directory located in the root of the project.

## Installing the required dependencies

Installing the required dependencies should be as easy as:

`pip3 install -r requirements.txt`

Use a venv if necessary.

## Using SiNRI

SiNRI consists of several individual modules that may be used
together. Most of the .py-files contain a main entrypoint, such that
the component can be launched standalone with command line arguments
(launch the scripts with --help to get a list of such
arguments). Launching all the scripts may become cumbersome,
especially if you do not know what all the components are meant to be
doing. Consult the GUI documentation if you don't want to bother with
this.

### meamer.py

The MEAMEr class is responsible for communication with a remote meame
host. The main functionality thus consists of acquiring data from the
DAQ, and forwarding stimuli to the DSP. `initialize_DAQ` will ready
the DAQ to output stream samples, and `recv_segment` can be used to
continually receive full segments for single channels. Example usage
of a MEAMEr object can be found in Grinder. The module contains no
main entrypoint, and should be used to delegate the responsibility of
MEAME communication.

### grinder.py

Grinder is the demultiplexer of the system, and supports listening to
both a live stream, and a recording contained in an HDF5-file (the act
of actually receiving these streams is delegated to PlaybackStream and
LiveStream objects). A Grinder server can be started as such:

`server = Server(8080, reflect=args.reflect, meame_addr=args.live)`

This will start a Grinder server running on port 8080, which will
reflect all channels to connecting hosts instead of demultiplexing
(e.g. to use with Cleaviz). An IP-address for a remote MEAME server
must also be supplied.

### mock.py

If development of SiNRI is to be done without a remote MEAME server
avaiable, the mock server can be used in its place. A mock can be initialized:

```
mock = MEAMEMock(12340)
mock.run()
```

Currently the recording is hard coded to reside in mea_data/1.h5,
which is a bit unfortunate. However, changing this to a command line
flag with argparse should pose few problems.

### cleaviz.py

Cleaviz is a visualization tool created to be able to see incoming
data streams in real time. This may serve as an invaluable debugging
tool, as it makes it quite easy to see whether streams are
demultiplexed in a wrong manner (e.g. by looking at the grounded
channel). Cleaviz requires a running Grinder server (currently hard
coded as running on port 8080 on the local host), and can be launched
like this:

```
win = CleavizWindow(sample_rate=10000, segment_length=args.segment_length)
win.run()
```

### analysis.py

The analysis module contains several examples of methods to analyze
incoming data streams, and should be fairly self-explanatory.

### Sensor

Arduino and ROS-code is available in the /sensor directory. The sensor
in use is the HC-SR04 ultrasound sensor, used with Arduino UNO, of
which there exists quite a few setup guides online.

### Lacking functionality for settings and error handling

The error handling of SiNRI is currently not quite optimal. Logging
facilities are included, but very few custom exception handlers have
been written, thus making most errors a bit too general. Settings
should in the future be moved to a single place, such that settings
such as chosen channels are not scattered all over the place. It
works, but may be confusing for someone a bit more unfamiliar with the
system.

## The GUI

The GUI is created as an easier-to-use alternative to launching
several scripts to use SiNRI. `python3 gui.py` launches the Qt
application, which can be used to start mock, Grinder and Cleaviz, as
well to display the functionality of several analysis tools.

## Demo project

demo_receiver.py contains a live demo of the system. This is a
closed-loop, where input from an external ultrasound sensor is used to
apply stimulation to a neural chamber. The output from MEAME is
analyzed to determine whether stimuli has been applied. This
illustrates end-to-end usage of the SiNRI system, where it is used in
its entirety to both apply stimulation and analyze the behaviour of a
natural neural network.