import threading


class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self.should_stop = threading.Event()


    def stop(self):
        self.should_stop.set()


    def stopped(self):
        return self.should_stop.is_set()


def check_terminate_thread():
    current_thread = threading.current_thread()
    if type(current_thread) == StoppableThread and current_thread.stopped():
        return True