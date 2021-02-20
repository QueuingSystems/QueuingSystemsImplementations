
from queue import Queue, Empty, Full 


import threading 
import sched, time
import numpy as np
from enum import Enum

import req

import distribution
import time


class QueuingSystem:

	class CharacterParam(Enum):
		TIME 			= 0
		COUNT 			= 1


	def __init__(self, length_of_queue, rho, number, lamb):
		self._queue_len 		= length_of_queue 		# максимальная длина очереди
		self._rho				= rho					# 
		self._number 			= number				# число генерируемых заявок
		self._lambda			= lamb					# плотность входного потока

		#self.no_waiting 		= 0		
		self._queue_len_proc	= 0		
		self._max_len 			= 0
		self._len_sum 			= 0
		self._added_number		= 0						# число добавленных заявок
		self._processed_number	= 0						# число обработанных заявок
		self._no_waiting_number	= 0						# число заявок вне очереди
		self.proc_thread_blocked= False
		self._ignored_number	= 0
		self._queue_len_array    = [] 
		#self.processed 			= 0
		#self.empty_processing_count = 0

		#self.real_try_proc_count = 0

		# Создание расписания:
		self.requests_shedule 	= sched.scheduler() # расписание добавления заявок в очередь
		self.processing_shedule = sched.scheduler() # расписание начала обработки заявок

		# Итак, сама очередь:
		self.requests_queue 	= Queue(self._queue_len)			# объект очереди
		self.requests_arr 		= []				# массив заявок, он формируется при добавлении заявки в очередь 


	# ========= Распределения: =========

	# Создание массива со временем добавления заявок в очередь:
	def generate_input_time_array (self, distr: distribution.TypeDistribution):
		#self._in_time_arr 		= distribution.generate_time_array(distr, self._number, self._rho, self._lambda)
		self._in_time_arr = np.random.exponential(1/self._lambda, self._number)

	# Создание массива со временем начала обработки заявок:
	def generate_output_time_array (self, distr: distribution.TypeDistribution):
		self._out_time_arr 		= distribution.generate_time_array(distr, self._number, self._rho, self._lambda)


	# ========= Работа с очередью: =========
	
	# Поступление заявки:
	def add_in_fifo(self):
		cur_req = req.Req()
		try:
			self.requests_queue.put(cur_req, block=False) # добавляем в очередь зявку
		except Full:
			cur_req.ignore()
			self._ignored_number += 1
		else:
			self._added_number += 1
		finally:
			self.requests_arr.append(cur_req) 			# запоминаем объект
			#print(self._added_number)



	# Обработка заявки:
	def get_from_fifo(self, processing_time):

		try:
			cur_req = self.requests_queue.get(block=False)
		except Empty:
			cur_req = self.requests_queue.get(block=True)
			cur_req.no_wait_in_queue()
		finally:
			cur_req.start_processing()
			time.sleep(processing_time)						# время обработки заявки задается сгенерированным значением
			cur_req.finish_processing()
			self._processed_number += 1

			#print(self._processed_number)


	# ========= Для потоков:: =========

	# функция для потока, который добавляет в очередь заявки:
	def generate_requests(self):
		for cur_time in self._in_time_arr:
			time.sleep(cur_time)
			self.add_in_fifo()

	# функция для потока, который вытаскивает заявки из очереди:
	def processing(self):
		for cur_time in self._out_time_arr:
			if self.req_thread.isAlive() or self._added_number > self._processed_number or self._added_number == 0:
				self.get_from_fifo(cur_time)

	# функция для потока, проверяющего длину очереди
	def testing_queue_len(self, interval):
		while self.proc_thread.isAlive() or self.req_thread.isAlive():
			current_len = self.requests_queue.qsize()
			self._max_len = max(current_len, self._max_len)
			self._len_sum += current_len
			self._queue_len_proc += 1

			time.sleep(interval)



	# Запуск очереди
	def run(self, requests_distribution, processing_distribution):
		self.generate_input_time_array(distr = requests_distribution)
		self.generate_output_time_array(distr = processing_distribution)

		testing_interval = min(self._in_time_arr) / 2
		self._init_time = time.monotonic()

		self.req_thread 	= threading.Thread(target=self.generate_requests, args=())
		self.proc_thread 	= threading.Thread(target=self.processing, args=())
		test_len_thread 	= threading.Thread(target=self.testing_queue_len, args=(testing_interval,))

		self.req_thread.start()
		test_len_thread.start()
		self.proc_thread.start()


		self.req_thread.join()
		self.proc_thread.join()




	# ========= Характеристики: =========

	# rho теоретическое:
	def get_generated_rho(self):
		return self._out_time_arr.mean() / self._in_time_arr.mean()

	# rho практическое:
	def get_real_rho(self):
		req_time 			= 0 # сумма в секундах времен генерации запросов от запуска программы
		proc_time			= 0 # сумма в секундах времен начала обработки от запуска программы
		prev_gen_time		= self._init_time

		for cur_req in self.requests_arr:
			req_time 		+= cur_req.get_generating_time() - prev_gen_time
			proc_time  		+= cur_req.get_processing_time()

			prev_gen_time 	= cur_req.get_generating_time()

		return proc_time / req_time

	# Подсчёт среднего времени обработки в очереди:
	def get_mean_processing_time(self):
		return sum(cur_req.get_processing_time() for cur_req in self.requests_arr) / len(self.requests_arr)

	# Подсчёт среднего времени ожидания в очереди:
	def get_mean_waiting_time(self):
		return sum(cur_req.get_waiting_time() if (not cur_req.is_ignored()) else 0 for cur_req in self.requests_arr) / len(self.requests_arr)

	# Подсчёт среднего размера очереди:
	def get_mean_queue_len(self):
		return self._len_sum / self._queue_len_proc

	# Максимальный размер очереди:
	def get_max_queue_len(self):
		return self._max_len

	# Коэффициент загруженности очереди:
	def get_load_factor(self):
		flag = False
		free_time_counter 	= 0
		
		for cur_req in self.requests_arr:
			if (not flag) and cur_req.is_no_wait_in_queue():
				flag = True
				mark = cur_req.get_generating_time()

			elif flag and not cur_req.is_no_wait_in_queue():
				flag = False
				free_time_counter += cur_req.get_generating_time() - mark		
		
		all_working_time = self.working_time()

		return (all_working_time - free_time_counter) / all_working_time

	# Число заявок, обслуженных без очереди:
	def get_no_waiting_req_number(self):
		count = 0

		for cur_req in self.requests_arr:
			if cur_req.is_no_wait():
				count = count + 1

		return count

	# Число заявок, которые не попали в очередь:
	def get_no_processing_number(self):
		return self._number - self._added_number 
		
	def run_with_timeout(self, timeout=600, period=0.25):
		self.generate_input_time_array(distribution.TypeDistribution.EXPONENTIAL)
		self.generate_output_time_array(distribution.TypeDistribution.EXPONENTIAL)
		
		testing_interval = self._in_time_arr.mean() 
		self._init_time = time.monotonic()

		self.req_thread 	= threading.Thread(target=self.generate_requests, args=())
		self.proc_thread 	= threading.Thread(target=self.processing, args=())
		test_len_thread 	= threading.Thread(target=self.testing_queue_len, args=(testing_interval,))

		self.req_thread.start()
		test_len_thread.start()
		self.proc_thread.start()

		end_timeout = self._init_time + timeout
		exit_flag 	= False
		finished	= False

		while not  exit_flag:
			finished = not (self.req_thread.isAlive() or self.proc_thread.isAlive()) 
			exit_flag = finished or time.monotonic() > end_timeout
			time.sleep(period)

		return finished
		
	def working_time (self):
		return self.requests_arr[len(self.requests_arr) - 1].get_finish_processing_time()  - self._init_time