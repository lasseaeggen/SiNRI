from McsPy import McsData
import socket
import threading


class Experiment(object):
    def __init__(self, h5_file):
        self.data = McsData.RawData(h5_file)
        self.stream = self.data.recordings[0].analog_streams[0]


    def get_channel_data(self, ch):
        return self.stream.get_channel_in_range(ch, 0, self.stream.channel_data.shape[1])


class Server(object):
    def __init__(self, port):
        self.host = '0.0.0.0'
        self.port = port
        self.experiment = Experiment('mea_data/1.h5')


    def listen(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket.bind((self.host, self.port))
            print('[INFO]: Server started on {host}:{port}'.format(host=self.host, port=self.port))
        except Exception as e:
            print('[ERROR]: Could not bind to port {port}'.format(port=self.port))
            print('[ERROR]: {e}'.format(e=e))
            return

        try:
            self.socket.listen(5)
            while True:
                (client, addr) = self.socket.accept()
                client.settimeout(60)
                print('[INFO]: Received connection from {addr}'.format(addr=addr))
                threading.Thread(target=self.handle_client, args=(client, addr)).start()
        except (KeyboardInterrupt, SystemExit):
            print('[INFO]: Shutdown request detected, shutting down gracefully')
            self.socket.shutdown(socket.SHUT_RDWR)


    def handle_client(self, client, addr):
        while True:
            data = client.recv(16)
            print('Received {data}'.format(data=data))

            if data:
                client.sendall(data)

            if data == b'q\n':
                client.close()
                break


def main():
    server = Server(8080)
    server.listen()


if __name__ == '__main__':
    main()
