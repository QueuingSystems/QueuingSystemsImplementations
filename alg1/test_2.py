import numpy as np
import timeit
import pandas as pd
from collections import deque, namedtuple
from enum import Enum
from tqdm import tqdm, trange

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
    for n in trange(1000, 52000, 1000):
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
    results = []
    for datum in tqdm(l_data):
        states, processed, passed_events, denied = process_queue(
            datum['req'], datum['srv'])
        time_total = 0
        QA = 0
        for i in range(len(states) - 1):
            time_delta = states[i + 1].time - states[i].time
            time_total += time_delta
            QA += states[i].req_number * time_delta
        QA /= time_total
        QT = np.mean([req.time_sp - req.time_in for req in processed])
        results.append({"N": datum["N"], "QA": QA, "QT": QT})

    df = pd.DataFrame(results)
    return df


if __name__ == '__main__':
    l_data = generate_length_test()
    df_l = test_length(l_data)
    df_l.to_csv('stats_pavel.csv', index=False)
