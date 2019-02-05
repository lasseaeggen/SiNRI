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

    rows = 6
    cols = 10
    plots = []
    for i in range(rows):
        for j in range(cols):
            plots.append(win.addPlot(row=i, col=j))
            plots[i*cols+j].setYRange(-10**(-4), 10**(-4), padding=0)
            plots[i*cols+j].hideAxis('left')
            plots[i*cols+j].hideAxis('bottom')

    # Create a callback for plot clicks to select a single channel.
    zoomed_plot = None
    def on_click(event):
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
            x_axis_data = [x for x in range(len(channel_data))]

            # Plot the actual data every second (for now).
            if zoomed_plot:
                segment_counter = (segment_counter + 1) % 5
                if segment_counter == 0:
                    zoomed_plot.plot(x_axis_data, channel_data, clear=True)
                    pg.QtGui.QApplication.processEvents()
            else:
                segment_counter = (segment_counter + 1) % 50
                if segment_counter == 0:
                    for i in range(rows):
                        for j in range(cols):
                            plots[i*cols+j].plot(x_axis_data, channel_data, clear=True)
                    pg.QtGui.QApplication.processEvents()

            # Reset for next segment.
            segment_data = bytearray(b'')
            bytes_received = 0


if __name__ == '__main__':
    main()
