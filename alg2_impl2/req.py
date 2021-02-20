import time # время в секундах,
# monotic -- следующее значение гарантиированно больше предыдущего

class Req:
	def __init__(self):
		self.generating_time		= time.monotonic()
		self.in_queue_time			= -1.0
		self.start_processing_time	= -1.0
		self.end_processing_time	= -1.0
		self.ignored 				= False
		self.no_wait				= False

# Ставим метки времени:
	# Добавление в очередь - поступление заявки в очередь:
	def add_in_queue(self):
		self.in_queue_time 			= time.monotonic()

	# Вывод заяки из очереди - начало обработки:
	def start_processing(self):
		self.start_processing_time	= time.monotonic()

	# Окончание обработки заявки:
	def finish_processing(self):
		self.end_processing_time	= time.monotonic()

# Получаем информацию:
	# Получаем время обрааботки заявки - от выхода из очереди ожидания до окончания выполнения действий:
	def get_processing_time(self):
		return self.end_processing_time - self.start_processing_time

	# Получаем время выхода заявки из очереди - начала обработки:
	def get_start_processing_time(self):
		return self.start_processing_time

	# Получаем время создания заявки:
	def get_generating_time(self):
		return self.generating_time
		
	# Получаем время ожидания заявки в очереди:	
	def get_waiting_time(self):
		return self.start_processing_time - self.generating_time

	# Поступила ли заявка на обработку сразу (с заданной погрешностью)
	def is_no_wait_in_queue(self, err = 0.0001):
		return abs(self.start_processing_time - self.generating_time) < err

	# Получаем время создания заявки:
	def get_finish_processing_time(self):
		return self.end_processing_time

	def ignore(self):
		self.ignored = True

	def is_ignored(self):
		return self.ignored

	def no_wait_in_queue(self):
		self.no_wait = True

	def is_no_wait(self):
		return self.no_wait