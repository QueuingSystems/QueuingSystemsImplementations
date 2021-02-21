import numpy as np
from collections import deque, namedtuple
from enum import Enum

RNG = np.random.default_rng()


def make_exp(l_, N):
    return [-np.log(1 - RNG.random()) / l_ for _ in range(N)]


EXP_L = 100
RHO = 0.75
exp_lambda = lambda rho: EXP_L / rho

N = 5000
Q = 10

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


def make_experiment(datum):
    states, processed, passed_events, denied = process_queue(
        datum['req'], datum['srv'], datum['q'])
    QM = np.max([state.req_number for state in states])
    QA = 0
    FR = 0
    time_total = 0
    for i in range(len(states) - 1):
        time_delta = states[i + 1].time - states[i].time
        time_total += time_delta
        QA += states[i].req_number * time_delta
        if states[i].req_number > 0:
            FR += time_delta

    QA = QA / time_total
    FR = FR / time_total
    QZ = len([req for req in processed if req.time_in == req.time_sp])
    QD = len(denied) / (len(processed) + len(denied))
    QT = np.mean([req.time_sp - req.time_in for req in processed])
    QX = np.mean([
        req.time_sp - req.time_in for req in processed
        if req.time_sp != req.time_in
    ])
    FT = np.mean([req.time_out - req.time_sp for req in processed])

    return {
        "QM": QM,
        "QA": QA,
        "QZ": QZ,
        "QD": QD,
        "QT": QT,
        "QX": QX
    }, {
        "FR": FR,
        "FT": FT
    }


if __name__ == '__main__':
    req = make_exp(EXP_L, N)
    srv = make_exp(exp_lambda(RHO), N)
    datum = {
        "req": req,
        "srv": srv,
        "q": Q
    }
    result = make_experiment(datum)
    print(result)
