import socket
import struct


def main():
    # Hard code these for now, use argparse maybe later? We are just
    # testing that we are receiving something at all, really.
    address = 'localhost'
    port = 8080

    # sample_rate * tick_rate, hard coded for now.
    data_per_tick = int(10000 * 0.01)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((address, port))
        channel_data = bytearray(b'')
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
                print(i)

            channel_data.extend(segment_data)
            segment_data = bytearray(b'')
            bytes_received = 0


if __name__ == '__main__':
    main()
