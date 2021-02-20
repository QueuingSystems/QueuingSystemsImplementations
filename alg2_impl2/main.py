from scipy.stats import uniform, expon,triang

from queue import Queue # и очередь, и стек, но нам нужна только очередь
# обычная очередь синхронизированная, блокирующая -- нам эти сложности ни к чему

from time import sleep 

import threading 
import sched, time

import req
from queuing_system import QueuingSystem as qs
import distribution

NUMBER 		= 1000
RHO			= 0.55
LAMBDA_IN 	= 100
LENGTH_OF_QUEUE = int(1e6)

processing_system = qs(length_of_queue = LENGTH_OF_QUEUE, rho=RHO, lamb=LAMBDA_IN, number=NUMBER)
processing_system.run(distribution.TypeDistribution.EXPONENTIAL, distribution.TypeDistribution.EXPONENTIAL)

print('rho, задан: ', processing_system._rho)
print('rho, теор : ', processing_system.get_generated_rho())
print('rho, практ: ', processing_system.get_real_rho())

print('QM, Максимальный размер очереди: ', 				processing_system.get_max_queue_len())
print('QA, Средний размер очереди: ', 					processing_system.get_mean_queue_len())
print('QZ, Число заявок, обслуженных без очереди: ', 	processing_system.get_no_waiting_req_number())
print('QT, Среднее время ожидания в очереди: ', 		processing_system.get_mean_waiting_time())

print('FR, Коэффициент загрузки очереди: ', 			processing_system.get_load_factor())
print('FT, Среднее время обслуживания заявки: ', 		processing_system.get_mean_processing_time())
print('Отклоненные заявки: ',					 		processing_system.get_no_processing_number())
