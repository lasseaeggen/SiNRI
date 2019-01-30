from McsPy import McsData
import socket


class McsLoader:
    def __init__(self, h5_file):
        self.data = McsData.RawData(h5_file)
        self.stream = self.data.recordings[0].analog_streams[0]


    def get_channel_data(self, ch):
        return self.stream.get_channel_in_range(ch, 0, self.stream.channel_data.shape[1])


def main():
    killer = GracefulKiller()
    h51 = McsLoader('mea_data/1.h5')

    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(('0.0.0.0', 6969))
    serversocket.listen(5)

    h51.get_channel_data(0)

    while True:
        print('waiting for a connection')
        connection, client_address = serversocket.accept()
        try:
            print('client connected:', client_address)
            while True:
                data = connection.recv(16)
                print('received {!r}'.format(data))
                if data:
                    connection.sendall(data)
                else:
                    break

                if data == b'quit\n':
                    connection.close()
                    break
        finally:
            connection.close()


if __name__ == '__main__':
    main()
