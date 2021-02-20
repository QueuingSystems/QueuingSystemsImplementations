
import numpy as np
from enum import Enum

class TypeDistribution(Enum):
	UNIFORM 		= 0
	EXPONENTIAL 	= 1
	TRIANGULAR 		= 2

# генерация значений по различным законам распределения:
def uniform 	(rho, lamb, number):
	return np.random.uniform(0, 2 * rho / lamb, number)
def uniform_special 	(a, b, number):
	return np.random.uniform(a, b, number)

def exponential (rho, lamb, number):
	return np.random.exponential(rho/lamb, number)
def exponential_special (param, number):
	return np.random.exponential(param, number)

def triangular 	(rho, lamb, number):
	return np.random.triangular(0, 0, 3 * rho / lamb, number)
def triangular_special 	(a, b, c, number):
	if c > a:
		a, c = c, a
	elif c == a:
		c = c + 0.00001
	return np.random.triangular(a, b, c, number)

# Выбор закона распределения
def generate_time_array (distr : TypeDistribution, number, rho, lamb):

	if distr == TypeDistribution.UNIFORM:
		return uniform (rho, lamb, number)

	if distr == TypeDistribution.EXPONENTIAL:
		return exponential (rho, lamb, number)

	return triangular(rho, lamb, number)

# Выбор закона распределения
def generate_time_array_special (distr : TypeDistribution, number, param = 1, a = 0, b = 0, c = 0):

	if distr == TypeDistribution.UNIFORM:
		return uniform_special (a, b, number)

	if distr == TypeDistribution.EXPONENTIAL and not param == 0:
		return exponential_special (1 / param, number)

	return triangular_special(a, b, c, number)