class SlidingWindow:
    def __init__(self, window_size):
        self.window_size = window_size
        self.start = 0
        self.end = 0
    
    def can_slide(self):
        return (self.end - self.start) <= window_size
    
    def increment_start(self):
        self.start += 1

    def increment_end(self):
        if self.can_slide():
            self.end += 1
            return True
        else:
            return False