class SlidingWindow:
    def __init__(self, window_size, array_size):
        self.window_size = window_size
        self.array_size = array_size
        self.start = 0
        self.end = 0
    
    def can_slide(self):
        return (self.end - self.start) <= window_size
    
    def increment_start(self):
        self.start = min(self.start + 1, self.array_size - 1)

    def increment_end(self):
        if self.can_slide():
            self.end = min(self.end + 1, self.array_size - 1)
            return True
        else:
            return False
    
    def finished(self):
        return self.start == self.array_size - 1 and self.end == self.array_size - 1