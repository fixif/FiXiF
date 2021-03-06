# coding: utf8

# This class describes a SISO transfer function
from numpy.random.mtrand import randint, rand
# from scipy.weave import inline

__author__ = "Thibault Hilaire"
__copyright__ = "Copyright 2015, FiXiF Project, LIP6"
__credits__ = ["Thibault Hilaire"]

__license__ = "GPL v3"
__version__ = "0.4"
__maintainer__ = "Thibault Hilaire"
__email__ = "thibault.hilaire@lip6.fr"
__status__ = "Beta"


from fixif.WCPG import WCPG_TF
from numpy import ndenumerate, array, linspace
from numpy import matrix as mat, polymul, polyadd
from numpy import diagflat, zeros, ones, r_, atleast_2d, fliplr
from scipy.signal import tf2ss, TransferFunction, dbode
from scipy.linalg import norm


class dTF(object):

	def __init__(self, num, den):
		"""
		Define a discrete-time SISO transfer function as

		:math:`H(z) = \frac{\sum_i^n num[i] z^-i}{1 + \sum_i^n den[i] z^-i}`
		"""

		den = mat(den)
		num = mat(num)

		if (num.shape[0] != 1) or (den.shape[0] != 1):
			raise ValueError('dTF: num and den should be 1D matrixes')

		# we normalize if den[0] is not equal to 1
		if den[0, 0] == 0:
			raise ValueError('dTF: The 1st coefficient of the denominator cannot be ZERO !')
		else:
			self._num = num/den[0, 0]
			self._den = den/den[0, 0]

		# filter order
		# if den.shape!=num.shape:
		# 	raise ValueError( 'Numerator and denomintator must have same length !')

		self._order = num.shape[1]-1

		# cached sollya numerator and denominator
		self._sollya = None
		self._WCPG = None

	@property
	def num(self):
		return self._num

	@property
	def den(self):
		return self._den

	@property
	def order(self):
		return self._order


	def __str__(self):
		"""pretty print of the transfer function"""
		str_num = " + ".join(str(c)+"z^"+str(-j) if j > 0 else str(c) for (i, j), c in ndenumerate(self.num))
		str_den = " + ".join(str(c)+"z^"+str(-j) if j > 0 else str(c) for (i, j), c in ndenumerate(self.den))

		fraclen = max(len(str_num), len(str_den))
		sp_num = " "*int((fraclen - len(str_num)) / 2)
		sp_den = " "*int((fraclen - len(str_den)) / 2)

		str_tf = "\n"
		str_tf += " "*7 + sp_num + str_num + "\n"
		str_tf += "H(z) = " + '-'*fraclen + "\n"
		str_tf += " "*7 + sp_den + str_den + "\n"

		return str_tf

	def __neg__(self):
		"""returns -dTF"""
		return dTF(-self._num, self._den)

	def __mul__(self, other):
		"""multiply"""
		if type(other) in [int, float]:
			return dTF(self._num * other, self._den)
		elif isinstance(other, dTF):
			numer = polymul(self.num.A1, other.num.A1)
			denom = polymul(self.den.A1, other.den.A1)
			return dTF(numer, denom)
		else:
			raise ValueError("Cannot multiply a dTF with a %s", type(other))
	__rmul__ = __mul__  # lazy definition

	def __add__(self, other):
		"""addition"""
		if type(other) in [int, float]:
			return dTF(polyadd(self._num.A1, self._den.A1 * other), self._den)
		if isinstance(other, dTF):
			numer = polyadd(polymul(self._num.A1, other.den.A1), polymul(self._den.A1, other.num.A1))
			denom = polymul(self._den.A1, other.den.A1)
			return dTF(numer, denom)
		raise ValueError("Cannot add a dTF with a %s", type(other))
	__radd__ = __add__  # lazy definition

	def __sub__(self, other):
		"""substraction"""
		if type(other) in [int, float]:
			return dTF(polyadd(self._num.A1, -self._den.A1 * other), self._den)
		if isinstance(other, dTF):
			numer = polyadd(polymul(self._num.A1, other.den.A1), -polymul(self._den.A1, other.num.A1))
			denom = polymul(self._den.A1, other.den.A1)
			return dTF(numer, denom)
		raise ValueError("Cannot substract a dTF with a %s", type(other))

	def __rsub__(self, other):
		"""right substraction"""
		if type(other) in [int, float]:
			return dTF(polyadd(-self._num.A1, self._den.A1 * other), self._den)
		if isinstance(other, dTF):
			numer = polyadd(polymul(other.num.A1, self._den.A1), -polymul(other.den.A1, self._num.A1))
			denom = polymul(self._den.A1, other.den.A1)
			return dTF(numer, denom)


	def to_dTFmp(self):
		from fixif.LTI import dTFmp
		return dTFmp(self._num, self._den)

	def to_dSS(self, form="ctrl"):
		"""
		Transform the transfer function into a state-space
		Parameters:
			- form: controllable canonical form ('ctrl') or observable canonical form ('obs')

		"""
		# TODO: code it without scipy

		from fixif.LTI import dSS
		if form == 'ctrl':
			A = mat(diagflat(ones((1, self.order-1)), 1))
			A[self.order-1, :] = fliplr(-self.den[0, 1:])
			B = mat(r_[zeros((self.order-1, 1)), atleast_2d(1)])
			C = mat(fliplr(self.num[0, 1:]) - fliplr(self.den[0, 1:])*self.num[0, 0])
			D = mat(atleast_2d(self.num[0, 0]))
		elif form == 'obs':
			# TODO: to it manually!!
			A, B, C, D = tf2ss(array(self.num)[0, :], array(self.den)[0, :])
		else:
			raise ValueError('dTF.to_dSS: the form "%s" is invalid (must be "ctrl" or "obs")' % form)

		return dSS(A, B, C, D)


	def toTransferFunction(self):
		"""
		Convert the object to a scipy Transfer Function
		"""
		return TransferFunction(self.num.tolist()[0], self.den.tolist()[0], dt=1)


	def to_Sollya(self):
		"""
		Convert transfer function into two Sollya polynomials (numerator and denomitator)
		The result is cached in self._sollya
		Returns
		- num, den: (sollya object) numerator and denominator of the transfer function
		"""
		if not self._sollya:
			try:
				import sollya
			except ImportError:
				raise ImportError("Sollya and SollyaPython are required (but not installed) !")
			num = sollya.horner(sum(sollya.SollyaObject(x) * sollya._x_ ** i for i, x in enumerate(array(self.num)[0, :])))
			den = sollya.horner(sum(sollya.SollyaObject(x) * sollya._x_ ** i for i, x in enumerate(array(self.den)[0, :])))
			self._sollya = (num, den)
		return self._sollya


	def bode(self, wmin=1e-3, tikz=False):
		"""Plot a bode graph
		return tikz code if tikz is True, otherwise display it"""
		# get the frequency, magnitude and phase
		w, mag, phase = dbode(self.toTransferFunction(), linspace(wmin, 3.14159, 500))

		import matplotlib.pyplot as plt
		plt.figure(3)
		plt.subplot(2, 1, 1)
		plt.semilogx(w, mag, 'b-', linewidth=1)
		plt.xlim((wmin, 3.5))
		plt.grid(b=True, which='major', color='gray', linestyle='-')
		plt.grid(b=True, which='minor', color='silver', linestyle='--')
		plt.ylabel('Magnitude (dB)')
		plt.axvline(x=3.14159, color='grey', zorder=2)
		plt.subplot(2, 1, 2)
		plt.semilogx(w, phase, 'b-', linewidth=1)
		plt.xlim((wmin, 3.5))
		plt.grid(b=True, which='major', color='gray', linestyle='-')
		plt.grid(b=True, which='minor', color='silver', linestyle='--')
		plt.axvline(x=3.14159, color='grey', zorder=2)
		plt.ylabel('Phase')
		plt.xlabel('Frequency ($rad.s^{-1}$)')
		if tikz:
			import matplotlib2tikz
			return matplotlib2tikz.get_tikz_code(figurewidth='15cm', figureheight='7cm')
		else:
			plt.show()


	def assert_close(self, other, eps=1e-7):
		"""
		asserts that self is "close" to other
		ie the numerator and denominator are close
		Parameters
		----------
		other: dTF object
		eps:
		"""
		# add zeros for the smallest (in size) numerator so that the comparison can be done
		max_order = max(self.order, other.order)+1
		snum = zeros((1, max_order))
		snum[:1, :self.num.shape[1]] = self.num
		onum = zeros((1, max_order))
		onum[:1, :other.num.shape[1]] = other.num
		sden = zeros((1, max_order))
		sden[:1, :self.den.shape[1]] = self.den
		oden = zeros((1, max_order))
		oden[:1, :other.den.shape[1]] = other.den

		assert(norm(snum-onum) < eps)
		assert(norm(sden-oden) < eps)

	def WCPG(self):
		r"""
		Copute the Worst Case Peak Gain of a SISO filter described with its transfer function

		"""
		# compute the WCPG value if it's not already done
		if self._WCPG is None:
			self._WCPG = WCPG_TF(self._num, self._den)
		return self._WCPG


def iter_random_dTF(number, order=(5, 10)):
	"""
	Generate some n-th order random (stable or not) SISO transfer functions

	Parameters:
		- number: number of state-space to generate
		- order: tuple (mini,maxi) order of the filter (default:  random between 5 and 10)

	Returns:
		- returns a generator of dTF objects (to use in a for loop for example)

	..Example::
		#>>> sys = list( iter_random_dTF( 12, (10,20)) )
		#>>> for S in iter_random_dTF( 12, (10,20)):
		#>>>		print( S.num )

	"""
	for i in range(number):
		yield random_dTF(order)



def random_dTF(order=(5, 10)):
	"""
	Generate a n-th order random transfer function (not necessary stable)
	Parameters:
		- order: tuple (mini,maxi) order of the filter (default:  random between 5 and 10)
	"""
	if order[0] == order[1]:
		n = order[0]
	else:
		n = randint(*order)
	num = mat(rand(1, n))
	den = mat(rand(1, n))
	return dTF(num, den)


# def to_dSSmp(b, a, mpmatrices=True):
#
# 	"""
# 	Given a SISO transfer function numerator and denumerator in multiple precision,
# 	this function constructs a discrete state-space matrices in canonical controllable form[1].
# 	If mpmatrices is not True, return the state matrices in numpy format instead of MPmath.
#
# 	Requirements:
# 	1. numerator and denumenator are in the form of MPmath amtrices of size degree x 1
# 	2. denumerator must have its first coeff equal to 1.0 (by construction it must be true)
#
# 	Algorithm:
#
# 	1. Extract a delay-free path D = h(0) = b_0
# 	This is done by one stage of long division:
#
# 	H(z) = b_0 + { (beta_1 * z^-1 + ... + beta_N * z^-N} / {1 + a_1 * z^-1 + ... + a_N * z^-N},
#
# 	where
# 		N = max(Na, Nb)
# 		a_i = 0                     for i > Na
# 		b_i = 0                     for i > Nb
# 		beta_i = b_i - b_0 * a_i    for i=1...N
#
# 	2. Controller canonical form is as follows:
# 		-a_1    -a_2    ... -a_N-1    -a_N          1
# 		1       0                        0          0
# 	A = 0       1                        0      B=  0
# 						....                        ...
# 		0       0              1         0		    0
#
#
# 	C = [beta_1     beta_2  ... beta_N]         D = b_0
#
#
# 	[1] https://ccrma.stanford.edu/~jos/fp/Converting_State_Space_Form_Hand.html
# 	Parameters
# 	----------
# 	b           - numerator of a TF, in MPmath
# 	a           - denumerator of a TF, in MPmath
# 	mpmatrices  - set to False if want numpy matrices to be returned
#
# 	Returns
# 	-------
# 	A, B, C, D  - state-matrices of a discrete state-space in canonical form.
# 	"""
#
#
# 	#we need to store a and b as column vectors (because legacy)
# 	#if they are row vectors, just transpose them
# 	if a.rows == 1:
# 		a = a.transpose()
# 	if b.rows == 1:
# 		b = b.transpose()
#
# 	p = 1
# 	q = 1
# 	nb = b.rows
# 	na = a.rows
#
# 	if a[0,0] != mpmath.mpf('1.0'):
# 		raise ValueError('Cannot convert a MP transfer function to dSS: a[0] must be 1 but it is not.')
#
# 	alpha = a
# 	beta = b
# 	if na > nb:
# 		#if b is shorter than a, then we fill it with na-nb zeroes
# 		N = na
# 		beta = mp.zeros(N, 1)
# 		for i in range(0, nb):
# 			beta[i,0] = b[i]
# 	elif nb < na:
# 		# if a is shorter than b, then we fill it with na-nb zeroes
# 		# WARNING: a priori this should never be the case !!!
# 		N = nb
# 		alpha = mp.zeroes(N, 1)
# 		for i in range(0, na):
# 			alpha[i, 0] = a[i]
# 	else:
# 		#if a and b are of the same size
# 		N = nb
#
# 	A = mp.zeros(N-1, N-1)
# 	A[0,:] = -alpha.transpose()[0,1:N]
# 	for i in range(1, N-1):
# 		A[i,i-1] = mpmath.mpf('1.0')
# 	B = mp.zeros(N-1, 1)
# 	B[0,0] = mpmath.mpf('1.0')
#
#
# 	#We compute matrix C exactly
# 	C = mp.zeros(1, N-1)
# 	for i in range(0, N-1):
# 		tmp = mpmath.fmul(beta[0,0], alpha[i+1, 0], exact=True)
# 		C[0,i] = mpmath.fsub(beta[i+1,0], tmp, exact=True)
#
# 	D = mpmath.matrix([beta[0,0]])
#
#
# 	if not mpmatrices:
# 		A = mpf_to_numpy(A)
# 		B = mpf_to_numpy(B)
# 		C = mpf_to_numpy(C)
# 		D = mpf_to_numpy(D)
#
#
# 	return A,B,C,D
