from collections import deque


class JobQueue:

    def __init__(self):

        self.queue=deque()

    def add(self,job):

        self.queue.append(job)

    def next(self):

        if len(self.queue)==0:

            return None

        return self.queue.popleft()

    def clear(self):

        self.queue.clear()

    def empty(self):

        return len(self.queue)==0

    def size(self):

        return len(self.queue)

    def jobs(self):

        return list(self.queue)