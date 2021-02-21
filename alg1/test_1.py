import numpy as np
import timeit
import pandas as pd
from collections import deque, namedtuple
import multiprocessing
from enum import Enum
from tqdm import tqdm, trange
import os
import sys

RNG = np.random.default_rng()


def make_exp(l, N):
    return [-np.log(1 - RNG.random()) / l for _ in range(N)]


EXP_L = 100
RHO = 0.75
exp_lambda = lambda rho: EXP_L / rho

N = 5000

exp_lambda_2 = lambda rho, exp_l: exp_l / rho

CPU_N = 100000


def generate_length_test():
    data = []
    for n in trange(1000, 100000, 1000):
        data.append({
            "req": make_exp(EXP_L, n),
            "srv": make_exp(exp_lambda(RHO), n),
            "N": n
        })
    return data


QueueState = namedtuple('QueueState', ['req_number', 'time'])
Request = namedtuple('Request', ['time_in', 'time_sp', 'time_out', 'time_pr'])
Event = namedtuple('Event', ['time', 'type'])


class EvtType(Enum):
    PUSH = 1
    STOP = 2
    DENY = 3


def process_queue(in_s, out_s, max_size=None):
    assert len(in_s) == len(out_s)
    queue, states, processed, passed_events, denied = deque(), deque(), deque(
    ), deque(), deque()
    events = []
    in_times, out_times = deque(in_s), deque(out_s)
    time = 0
    processing = None
    while len(in_times) > 0 or len(events) > 0:
        if len(events) > 0 and events[0].time == time:
            evt = events.pop(0)
            passed_events.append(evt)
            if evt.type == EvtType.STOP:
                processing = processing._replace(time_out=time,
                                                 time_pr=time -
                                                 processing.time_sp)
                processed.append(processing)
                processing = None

            elif evt.type == EvtType.PUSH:
                req = Request(time_in=time,
                              time_out=None,
                              time_sp=None,
                              time_pr=None)
                if max_size is None or len(queue) < max_size:
                    queue.append(req)
                else:
                    denied.append(req)
                    passed_events.append(Event(time, EvtType.DENY))
                if len(in_times) > 0:
                    events.append(
                        Event(time + in_times.popleft(), EvtType.PUSH))

        if len(events) == 0 and len(in_times) > 0:
            events.append(Event(time + in_times.popleft(), EvtType.PUSH))

        if len(queue) > 0 and processing is None:
            processing = queue.popleft()._replace(time_sp=time)
            events.append(Event(time + out_times.popleft(), EvtType.STOP))

        states.append(QueueState(req_number=len(queue), time=time))
        events = sorted(events, key=lambda evt: evt.time)
        if len(events) > 0:
            time = events[0].time

    return states, processed, passed_events, denied


d = None


def test_length(l_data):
    global d
    results = []
    for datum in tqdm(l_data):
        d = datum
        r = min(
            timeit.repeat('process_queue(d["req"], d["srv"])',
                          globals=globals(),
                          number=1,
                          repeat=5))
        results.append({"n": datum["N"], "t": r})
    df = pd.DataFrame(results)
    return df


def generate_values_test():
    data = []
    for exp_l in tqdm(list(np.logspace(-5, 5, 100))):
        data.append({
            "mean": 1 / exp_l,
            "req": make_exp(exp_l, N),
            "srv": make_exp(exp_lambda_2(exp_l, RHO), N),
        })
    return data


def test_values(t_data):
    global d
    results = []
    for datum in tqdm(t_data):
        d = datum
        r = min(
            timeit.repeat('process_queue(d["req"], d["srv"])',
                          globals=globals(),
                          number=1,
                          repeat=5))
        results.append({"mean": datum["mean"], "t": r})
    df = pd.DataFrame(results)
    return df


def test_cpu():
    global req
    global srv
    req = make_exp(EXP_L, CPU_N)
    srv = make_exp(exp_lambda_2(EXP_L, RHO), CPU_N)
    cpu_cnt = multiprocessing.cpu_count()

    r = min(
        timeit.repeat("process_queue(req, srv)",
                      globals=globals(),
                      repeat=5,
                      number=1))

    if not os.path.exists('./cpu_pavel.csv'):
        with open('./cpu_pavel.csv', 'w') as f:
            f.write('cpu_cnt, r\n')

    with open('./cpu_pavel.csv', 'a') as f:
        f.write(f"{cpu_cnt},{r}\n")

    return r


if __name__ == '__main__':
    if ('--cpu-only' not in sys.argv):
        l_data = generate_length_test()
        df_l = test_length(l_data)
        df_l.to_csv('len_pavel.csv')

        t_data = generate_values_test()
        df_t = test_values(t_data)
        df_t.to_csv('t_pavel.csv')

    test_cpu()
