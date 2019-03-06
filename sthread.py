import threading


class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self.should_stop = threading.Event()


    def stop(self):
        self.should_stop.set()


    def stopped(self):
        return self.should_stop.is_set()
