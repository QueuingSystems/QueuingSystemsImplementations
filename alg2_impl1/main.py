import numpy as np
from threading import Timer
from multiprocessing import Process, Manager
from time import time, sleep
from collections import deque

ro_1, ro_2 = 0.5, 0.65
N1, N2 = 2000, 50000


lambda_ = 100
mu_1 = lambda_ / ro_1 
mu_2 = lambda_ / ro_2


class Queue_object():
    def __init__(self, without_queue = False, is_dropped=False, append_time=-1, queue_len=0):
        self.processing_without_queue = without_queue
        self.is_dropped = is_dropped
        self.append_time = append_time
        self.pop_time = None
        self.completed_time = None
        self.current_queue_len = queue_len
    
    def __repr__(self):
        return 'Queue object. is dropped: {}, queue len: {}, append: {}, pop: {}, process: {}, process without queue: {}'.format(self.is_dropped, self.current_queue_len, self.append_time, self.pop_time, self.completed_time, self.processing_without_queue)


class State():
    def __init__(self, append_time_intervals, processing_time_intervals, max_len=100):
        self.append_time_intervals = deque(append_time_intervals)
        self.processing_time_intervals = deque(processing_time_intervals)
        self.check_queue_interval = np.min(append_time_intervals)/2
        self.mean_append_time = self.check_queue_interval #np.mean(append_time_intervals)
        self.queue = deque(maxlen=max_len)
        self.is_processing = False
        self.completed_tasks = deque()
        self.queue_len = deque()
        self.still_compute_length = True
        self.statistics = None

    def append_process(self):
        current_queue_len = len(self.queue)
        is_dropped = (current_queue_len >= self.queue.maxlen)
        append_time = time()
        processing_without_queue = not self.is_processing
        obj = Queue_object(processing_without_queue, is_dropped, append_time, current_queue_len)
        if is_dropped:
            self.completed_tasks.append(obj)
        else:
            self.queue.append(obj)
        if self.append_time_intervals:
            Timer(self.append_time_intervals.popleft(), self.append_process).start()

    def remove_process(self):
        if self.queue:
            obj = self.queue.popleft()
            obj.pop_time = time()
            self.is_processing = True
            sleep(self.processing_time_intervals.popleft())
            obj.completed_time = time()
            self.completed_tasks.append(obj)
            self.is_processing = False
        if self.queue:
            self.remove_process()
        elif self.append_time_intervals or self.queue:
            Timer(self.check_queue_interval, self.remove_process).start()
        elif self.still_compute_length:
            Timer(self.check_queue_interval, self.remove_process).start()
            self.still_compute_length = False

    def len_process(self):
        if self.still_compute_length:
            self.queue_len.append(len(self.queue))
            Timer(self.mean_append_time, self.len_process).start()

    def compute_statistics(self):
        tasks = np.array(self.completed_tasks, dtype=Queue_object)
        not_dropped = tasks[[not task.is_dropped for task in tasks]]
        QM = np.max(self.queue_len)
        QA = np.mean(self.queue_len)
        QZ = np.sum([task.processing_without_queue for task in not_dropped])
        QT = np.mean([task.pop_time - task.append_time for task in not_dropped])
        QX = np.mean([task.pop_time - task.append_time for task in not_dropped if not task.processing_without_queue])
        proccessing_times = [task.completed_time - task.pop_time for task in not_dropped]
        FT = np.mean(proccessing_times)
        FR = np.sum(proccessing_times) / (not_dropped[-1].completed_time - not_dropped[0].append_time)
        return {
            'QM': round(QM, 6),
            'QA': round(QA, 6),
            'QZ': round(QZ, 6),
            'QT': round(QT, 6),
            'QX': round(QX, 6),
            'FT': round(FT, 6),
            'FR': round(FR, 6)
        }

    def compute_time(self):
        tasks = np.array(self.completed_tasks, dtype=Queue_object)
        not_dropped = tasks[[not task.is_dropped for task in tasks]]
        return max(tasks[-1].append_time, not_dropped[-1].completed_time) - tasks[0].append_time

    def start_processes(self):
        self.remove_process()
        self.append_process()
        self.len_process()

def wait_until(state, timeout=600, period=0.25):
    state.start_processes()
    start_time = time()
    mustend = start_time + timeout
    while time() < mustend:
        if not state.still_compute_length: 
            return True
        sleep(period)
    return False


if __name__ == "__main__":
    # mu = mu_1
    mu = lambda_ / 0.5
    N = 1000
    print('lambda: {}, mu: {}, size: {}'.format(lambda_, mu, N))
    append_intervals = np.random.exponential(1/lambda_,size=N-1)
    pop_intervals = np.random.exponential(1/mu,size=int(N))

    state = State(append_intervals, pop_intervals)
    result = wait_until(state, 600)
    result
    if result:
        stat = state.compute_statistics()
        time = state.compute_time()
        print(time, stat)
    else:
        print('fail computing')