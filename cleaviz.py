import channelconverter as chconv
import socket
import struct
import pyqtgraph as pg
import scipy.signal
import datetime
import json
import numpy as np


def main():
    # Hard code these for now, use argparse maybe later? We are just
    # testing that we are receiving something at all, really.
    address = 'localhost'
    port = 12340

    # sample_rate * tick_rate, hard coded for now.
    sample_rate = 10000
    tick_rate = 0.01
    data_per_tick = int(sample_rate * tick_rate)
    seconds = 3
    data_in_window = sample_rate*seconds // 10

    # Plot the received data in real time.
    app = pg.QtGui.QApplication([])
    win = pg.GraphicsWindow()
    win.setFixedSize(1200, 800)

    rows = 6
    cols = 10
    plots = []
    for i in range(rows):
        for j in range(cols):
            plots.append(win.addPlot(row=i, col=j))
            plots[i*cols+j].setYRange(-10**(-4), 10**(-4), padding=0)
            plots[i*cols+j].hideAxis('left')
            plots[i*cols+j].hideAxis('bottom')
            plots[i*cols+j] = plots[i*cols+j].plot()

    # Create a callback for plot clicks to select a single channel.
    zoomed_plot = None
    def on_click(event):
        # Ignore clicks that are not left-clicks.
        if event.button() != 1:
            return

        nonlocal plots
        nonlocal zoomed_plot

        if zoomed_plot:
            zoomed_plot = None

            # Go back to plotting all channels.
            win.clear()
            plots = []
            for i in range(rows):
                for j in range(cols):
                    plots.append(win.addPlot(row=i, col=j))
                    plots[i*cols+j].setYRange(-10**(-4), 10**(-4), padding=0)
                    plots[i*cols+j].hideAxis('left')
                    plots[i*cols+j].hideAxis('bottom')
                    plots[i*cols+j] = plots[i*cols+j].plot()
        else:
            clicked_items = win.scene().items(event.scenePos())
            zoomed_plot = [x for x in clicked_items if isinstance(x, pg.PlotItem)][0]
            x_axis = zoomed_plot.items[0].xData
            y_axis = zoomed_plot.items[0].yData

            # Add a new, singular plot to the window (zoomed in).
            win.clear()
            zoomed_plot = win.addPlot()
            zoomed_plot.plot(x_axis, y_axis, clear=True)
            zoomed_plot.setYRange(-10**(-4), 10**(-4), padding=0)
    win.scene().sigMouseClicked.connect(on_click)

    segment_counter = 0
    timer_counter = 0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((address, port))
        channel_data = {n: [] for n in range(60)}
        segment_data = bytearray(b'')
        bytes_received = 0

        # Write JSON formatted settings to the remote stream server.
        # s.send(json.dumps({
        #     'experiment': 'default',
        #     'channel': chconv.MCSChannelConverter.mcsviz_to_channel[12],
        # }).encode('utf-8'))

        while True:
            current_channel = 0
            while current_channel < 60:
                # We are receiving 4-byte floats.
                data = s.recv(data_per_tick*4 - bytes_received)
                bytes_received = bytes_received + len(data)
                segment_data.extend(data)

                if (bytes_received != data_per_tick*4):
                    continue

                # Print the received segment data.
                new_channel_data = []
                for i in struct.iter_unpack('f', segment_data):
                    new_channel_data.append(i[0])
                # TESTING DECIMATION
                ds = 20
                n = len(new_channel_data) // ds
                new1 = np.empty((n, 2))
                new2 = np.array(new_channel_data[:n*ds]).reshape((n, ds))
                new1[:, 0] = new2.max(axis=1)
                new1[:, 1] = new2.min(axis=1)
                new_channel_data = new1.reshape(n*2)

                channel_data[current_channel].extend(new_channel_data)
                channel_data[current_channel] = channel_data[current_channel][-data_in_window:]

                # Reset for next segment.
                segment_data = bytearray(b'')
                bytes_received = 0
                current_channel += 1

            # For the purpose of debugging of timing.
            timer_counter = (timer_counter + 1) % (sample_rate // data_per_tick)
            if timer_counter == 0:
                print(datetime.datetime.now())

            # Data to plot.
            x_axis_data = [x for x in range(len(channel_data[0]))]

            # Plot the actual data every second (for now).
            if zoomed_plot:
                segment_counter = (segment_counter + 1) % 5
                if segment_counter == 0:
                    zoomed_plot.plot(x_axis_data, channel_data[0], clear=True)
                    pg.QtGui.QApplication.processEvents()
            else:
                segment_counter = (segment_counter + 1) % 10
                if segment_counter == 0:
                    for i in range(rows):
                        for j in range(cols):
                            plots[i*cols+j].setData(x=x_axis_data, y=channel_data[i*cols+j])

                    pg.QtGui.QApplication.processEvents()


if __name__ == '__main__':
    main()
