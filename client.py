import socket
import struct
import pyqtgraph as pg
import random


def main():
    # Hard code these for now, use argparse maybe later? We are just
    # testing that we are receiving something at all, really.
    address = 'localhost'
    port = 8080

    # sample_rate * tick_rate, hard coded for now.
    sample_rate = 10000
    tick_rate = 0.01
    data_per_tick = int(sample_rate * tick_rate)

    # Plot the received data in real time.
    app = pg.QtGui.QApplication([])
    win = pg.GraphicsWindow()

    pw = win.addPlot()
    pw2 = win.addPlot()
    pw3 = win.addPlot()
    pw4 = win.addPlot()

    pw.setYRange(-10**(-4), 10**(-4), padding=0)
    pw2.setYRange(-10**(-4), 10**(-4), padding=0)
    pw3.setYRange(-10**(-4), 10**(-4), padding=0)
    pw4.setYRange(-10**(-4), 10**(-4), padding=0)

    segment_counter = 0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((address, port))
        channel_data = []
        segment_data = bytearray(b'')
        bytes_received = 0

        while True:
            # We are receiving 4-byte floats.
            data = s.recv(data_per_tick*4 - bytes_received)
            bytes_received = bytes_received + len(data)
            segment_data.extend(data)

            if (bytes_received != data_per_tick*4):
                continue

            # Print the received segment data.
            for i in struct.iter_unpack('f', segment_data):
                channel_data.append(i[0])

            # Slice data to only contain the last three seconds.
            seconds = 3
            channel_data = channel_data[-(sample_rate*seconds):]

            # Plot the actual data every 10th iteration.
            segment_counter = (segment_counter + 1) % 10
            if segment_counter == 0:
                pw.plot([x for x in range(len(channel_data))], channel_data, clear=True)
                pw2.plot([x for x in range(len(channel_data))], channel_data, clear=True)
                pw3.plot([x for x in range(len(channel_data))], channel_data, clear=True)
                pw4.plot([x for x in range(len(channel_data))], channel_data, clear=True)
                pg.QtGui.QApplication.processEvents()

            # Reset for next segment.
            segment_data = bytearray(b'')
            bytes_received = 0


if __name__ == '__main__':
    main()
