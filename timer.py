import time

class Timer:
    def __init__(self, duration):
        self.start_time = -1
        self.duration = duration

    def start(self):
        if self.start_time == -1:
            self.start_time = time.time()
    
    def stop(self):
        if self.start_time != -1:
            self.start_time = -1
    
    def running(self):
        return self.start_time != -1

    # Timer times out if current time and start time are greater than duration specified
    def timeout(self):
        if not self.running():
            return False
        else:
            return time.time() - self.start_time >= self.duration