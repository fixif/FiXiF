# coding: utf8

"""
This file contains Object and methods for a Discrete State Space
"""

__author__ = "Thibault Hilaire, Joachim Kruithof"
__copyright__ = "Copyright 2015, FiXiF Project, LIP6"
__credits__ = ["Thibault Hilaire", "Joachim Kruithof", "Anastasia Lozanova"]

__license__ = "GPL v3"
__version__ = "0.4"
__maintainer__ = "Thibault Hilaire"
__email__ = "thibault.hilaire@lip6.fr"
__status__ = "Beta"


from copy import copy
from numpy import empty, float64, identity, dot, array
from numpy import matrix as mat, set_printoptions
from numpy import eye, zeros, r_, c_, sqrt
from numpy.linalg import inv, solve, norm
from numpy.linalg.linalg import LinAlgError
from scipy.linalg import solve_discrete_lyapunov

from scipy.signal import ss2tf
from numpy.core.umath import pi, cos, sin
from numpy.random.mtrand import randint, rand, randn
import numpy
from itertools import chain
from numpy.testing import assert_allclose

from fixif.WCPG import WCPG_ABCD

try:
	from slycot import sb03md, ab09ad
except ImportError:
	pass


class dSS(object):
	r"""
	The dSS class describes a discrete state space realization

	A state space system :math:`(A,B,C,D)` is defined by

	.. math::

		\left\lbrace \begin{aligned}
		x(k+1) &= Ax(k) + Bu(k) \\
		y(k)   &= Cx(k) + Du(k)
		\end{aligned}\right.

	with :math:`A \in \mathbb{R}^{n \times n}, B \in \mathbb{R}^{n \times q},
	C \in \mathbb{R}^{p \times n} \text{ and } D \in \mathbb{R}^{p \times q}`.

	**Dimensions of the state space :**

	.. math::
		:align: left
		n,p,q \in \mathbb{N}

	==  ==================
	n   number of states
	p   number of outputs
	q   number of inputs
	==  ==================

	Additional data available, computed once when asked for :
	dSS.Wo, dSS.Wc, dSS.norm_h2, dSS.WCPG

	- Gramians : Wo and Wc
	- "Norms"   : H2-norm (H2norm), Worst Case Peak Gain (WCPG) (see doc for each)

	"""

	_W_method = 'slycot'  # linalg, slycot


	def __init__(self, A, B, C, D):
		"""
		Construction of a discrete state space

		.. TODO

			force docstring to appear in doc because calling spec is important
			add special section to document event_spec and examples
		"""

		self._A = mat(A)  # User input
		self._B = mat(B)
		self._C = mat(C)
		self._D = mat(D)

		# Initialize state space dimensions from user input
		(self._n, self._p, self._q) = self._check_dimensions()  # Verify coherence, set dimensions

		# Initialize Gramians
		self._Wo = None
		self._Wc = None

		# Initialize norms
		self._H2norm = None
		self._DC_gain = None
		self._WCPG = None


	# Properties
	@property
	def A(self):
		"""Returns the matrix A"""
		return self._A

	@property
	def B(self):
		"""Returns the matrix B"""
		return self._B

	@property
	def C(self):
		"""Returns the matrix C"""
		return self._C

	@property
	def D(self):
		"""Returns the matrix D"""
		return self._D

	@property
	def n(self):
		"""Returns the state size"""
		return self._n

	@property
	def p(self):
		"""Returns the number of outputs"""
		return self._p

	@property
	def q(self):
		"""Returns the number of inputs"""
		return self._q

	# Wc and Wo are computed only once
	@property
	def Wo(self):
		"""Returns the observability Gramian"""
		if self._Wo is None:
			self.calc_Wo()
		return self._Wo

	@property
	def Wc(self):
		"""Returns the controlability Gramian"""
		if self._Wc is None:
			self.calc_Wc()
		return self._Wc

	@property
	def size(self):
		"""Returns the size of state space, as a tuple (n,p,q)"""
		return self._n, self._p, self._q


	# ================================
	# Gramians (Wo, Wc) calculation
	# ================================
	def calc_Wo(self, method=None):
		"""
		Computes observers :math:`W_o`  with method 'method' :

		:math:`W_o` is solution of equation :
		.. math::
			A^T * W_o * A + C^T * C = W_o

		Available methods :

		- ``linalg`` : ``scipy.linalg.solve_discrete_lyapunov``, 4-digit precision with small sizes,
		1 digit precision with bilinear algorithm for big matrixes (really bad).
		not good enough with usual python data types

		- ``slycot`` : using ``slycot`` lib with func ``sb03md``, like in [matlab ,pydare]
		see http://slicot.org/objects/software/shared/libindex.html

		- ``None`` (default) : use the default method defined in the dSS class (dSS._W_method)

		..Example::

			>>> mydSS = random_dSS() ## define a new state space from random data
			>>> mydSS.calc_Wo('linalg') # use numpy
			>>> mydSS.calc_Wo('slycot') # use slycot
			>>> mydSS.calc_Wo() # use the default method defined in dSS

		.. warning::

			solve_discrete_lyapunov does not work as intended, see
			http://stackoverflow.com/questions/16315645/am-i-using-scipy-linalg-solve-discrete-lyapunov-correctl
			Precision is not good (4 digits, failed tests)

		"""

		if method is None:
			method = dSS._W_method

		if method == 'linalg':
			try:
				X = solve_discrete_lyapunov(self._A.transpose(), self._C.transpose() * self._C)
				self._Wo = mat(X)

			except LinAlgError as ve:
				if ve.info < 0:
					e = LinAlgError(ve.message)
					e.info = ve.info
				else:
					e = LinAlgError("dSS: Wo: scipy Linalg failed to compute eigenvalues of Lyapunov equation")
					e.info = ve.info
				raise e

		elif method == 'slycot':
			# Solve the Lyapunov equation by calling the Slycot function sb03md
			# If we don't use "copy" in the call, the result is plain false

			try:
				X, scale, sep, ferr, w = sb03md(self.n, -self._C.transpose() * self._C,
				                                copy(self._A.transpose()), eye(self.n, self.n), dico='D', trana='T')
				self._Wo = mat(X)

			except ValueError as ve:

				if ve.info < 0:
					e = ValueError(ve.message)
					e.info = ve.info
				else:
					e = ValueError("dSS: Wo: The QR algorithm failed to compute all the eigenvalues "
					               "(see LAPACK Library routine DGEES).")
					e.info = ve.info
				raise e
			except NameError:
				return self.calc_Wo('linalg')

		else:
			raise ValueError("dSS: Unknown method to calculate observers (method=%s)" % method)


	def calc_Wc(self, method=None):
		"""
		Computes observers :math:`W_c`  with method 'method' :

		:math:`W_c` is solution of equation :
		.. math::
			A * W_c * A^T + B * B^T = W_c

		Available methods :

		- ``linalg`` : ``scipy.linalg.solve_discrete_lyapunov``, 4-digit precision with small sizes,
		1 digit precision with bilinear algorithm for big matrixes (really bad).
		not good enough with usual python data types

		- ``slycot`` : using ``slycot`` lib with func ``sb03md``, like in [matlab ,pydare]
		see http://slicot.org/objects/software/shared/libindex.html

		- ``None`` (default) : use the default method defined in the dSS class (dSS._W_method)

		..Example::

			>>> mydSS = random_dSS() ## define a new state space from random data
			>>> mydSS.calc_Wc('linalg') # use numpy
			>>> mydSS.calc_Wc('slycot') # use slycot
			>>> mydSS.calc_Wo() # use the default method defined in dSS

		.. warning::

			solve_discrete_lyapunov does not work as intended, see
			http://stackoverflow.com/questions/16315645/am-i-using-scipy-linalg-solve-discrete-lyapunov-correctl
			Precision is not good (4 digits, failed tests)

		"""
		if method is None:
			method = dSS._W_method

		if method == 'linalg':
			try:
				X = solve_discrete_lyapunov(self._A, self._B * self._B.transpose())
				self._Wc = mat(X)

			except LinAlgError as ve:
				if ve.info < 0:
					e = LinAlgError(ve.message)
					e.info = ve.info
				else:
					e = LinAlgError("dSS: Wc: scipy Linalg failed to compute eigenvalues of Lyapunov equation")
					e.info = ve.info
				raise e

		elif method == 'slycot':
			# Solve the Lyapunov equation by calling the Slycot function sb03md
			# If we don't use "copy" in the call, the result is plain false

			try:
				X, scale, sep, ferr, w = sb03md(self.n, -self._B * self._B.transpose(),
				                                copy(self._A), eye(self.n, self.n), dico='D', trana='T')
				self._Wc = mat(X)

			except ValueError as ve:

				if ve.info < 0:
					e = ValueError(ve.message)
					e.info = ve.info
				else:
					e = ValueError("dSS: Wc: The QR algorithm failed to compute all the eigenvalues "
					               "(see LAPACK Library routine DGEES).")
					e.info = ve.info
				raise e
			except NameError:
				return self.calc_Wc(method='linalg')

		else:
			raise ValueError("dSS: Unknown method to calculate observers (method=%s)" % method)


	# ======================
	# Norms ccomputation
	# ======================

	def H2norm(self):
		r"""

		Compute the H2-norm of the system

		.. math::

			\langle \langle H \rangle \rangle = \sqrt{tr ( C*W_c * C^T + D*D^T )}


		"""
		# return cached value if already computed
		if self._H2norm is not None:
			return self._H2norm

		# otherwise try to compute it
		try:
			# less errors when Wc is big and Wo is small
			M = self._C * self.Wc * self._C.transpose() + self._D * self._D.transpose()
			self._H2norm = sqrt(M.trace())[0,0]
		except ValueError:  # TODO: check what kind of exception we need to catch here
			try:
				M = self._B.transpose() * self.Wo * self._B + self._D * self._D.transpose()
				self._H2norm = sqrt(M.trace())[0,0]
			except ValueError:
				raise ValueError("dSS: h2-norm : Impossible to compute M. Default value is 'inf'")

		return self._H2norm




	def WCPG_mp(self):
		r"""
		Compute the Worst Case Peak Gain of the state space

		.. math::
			\langle \langle H \rangle \rangle \triangleq |D| + \sum_{k=0}^\infty |C * A^k * B|

		Using algorithm developed in paper :
		[CIT001]_

		.. [CIT001]
			Lozanova & al., calculation of WCPG

		"""
		# compute the WCPG value if it's not already done
		if self._WCPG is None:

			try:
				# noinspection PyUnusedLocal
				A, B, C, D = array(self._A), array(self._B), array(self._C), array(self._D)
				n, p, q = self.size
				W = empty((p, q), dtype=float64)
				mpeps = 2**-120

				# int WCPG_ABCD_mprec(mpfr_t *W, double *A, double *B, double *C, double *D, uint64_t n, uint64_t p, uint64_t q, mpfr_t mpeps);
				code = "return_val = WCPG_ABCD( &W[0,0], &A[0,0], &B[0,0], &C[0,0], &D[0,0], n, p, q, mpeps);"
				support = 'extern "C" int WCPG_ABCD_mprec(double *W, double *A, double *B, double *C, double *D, ' \
				          'uint64_t n, uint64_t p, mpfr_t mpeps);'
				err = inline(code, ['W', 'A', 'B', 'C', 'D', 'n', 'p', 'q', 'mpeps'], support_code=support, libraries=["WCPG"])
				if err == 0:
					# change numpy display formatter, so that we can display the full coefficient in hex
					# (equivalent to printf("%a",...) in C)
					set_printoptions(formatter={'float_kind': lambda x: x.hex()})
					print(self)
					raise ValueError("WCPG: cannot compute WCPG")
				self._WCPG = mat(W)
			except:
				raise ValueError("dSS: Impossible to compute WCPG matrix. Is WCPG library really installed ?")

		return self._WCPG


	def WCPG(self, output_info=None):
		r"""
		Compute the Worst Case Peak Gain of the state space
		if output_info is given, it should be a dictionary that will be fill by WCPG library.
		It then contains some informations about the computation (nb iterations, etc.)
		.. math::
			\langle \langle H \rangle \rangle \triangleq |D| + \sum_{k=0}^\infty |C * A^k * B|

		Using algorithm developed in paper, and implement in the WCPG library (and its Python wrapper) :

		"""
		# compute the WCPG value if it's not already done
		if self._WCPG is None or output_info is not None:
			self._WCPG = WCPG_ABCD(self._A, self._B, self._C, self._D, output_info)
		return self._WCPG




	# ======================================================================================
	def calc_DC_gain(self):
		r"""
		Compute the DC-gain of the filter

		.. math::
			\langle H \rangle = C * (I_n - A)^{-1} * B + D

		"""
		# compute the DC gain if it is not already done
		if self._DC_gain is None:
			try:
				self._DC_gain = self._C * inv(identity(self._n) - self._A) * self._B + self._D
			except LinAlgError:
				raise ValueError('dSS: Impossible to compute DC-gain from current discrete state space')

		return self._DC_gain



	def similarity(self, T):
		"""
		Apply a similarity transform T
		"""
		#TODO: check T size
		#TODO: check computational errors !
		Tinv = inv(T)
		self._A = Tinv * self._A * T
		self._B = Tinv * self._B
		self._C = self._C * T
		# D is unchanged

	# ======================================================================================
	def _check_dimensions(self):
		"""
		Computes the number of inputs and outputs.
		Check for concordance of the matrices' size
		"""

		# A
		a1, a2 = self._A.shape
		if a1 != a2:
			raise ValueError('dSS: A is not a square matrix')
		n = a1

		# B
		b1, b2 = self._B.shape
		if b1 != n:
			raise ValueError('dSS: A and B should have the same number of rows')
		inputs = b2

		# C
		c1, c2 = self._C.shape
		if c2 != n:
			raise ValueError('dSS: A and C should have the same number of columns')
		outputs = c1

		# D
		d1, d2 = self._D.shape
		if d1 != outputs or d2 != inputs:
			raise ValueError('dSS: D should be consistent with C and B')

		return n, outputs, inputs


	# ======================================================================================
	def __str__(self):
		"""
		Display the state-space
		"""
		# def tostr(M, name):
		# 	"""Returns a string representation of the value, except if it's None"""
		# 	if M is not None:
		# 		return name + "= " + repr(M) + "\n"
		# 	else:
		# 		return name + " is not computed\n"

		def plural(n):
			"""Give the plural form (a s or not)"""
			return 's' if n > 0 else ''

		size = [(x, plural(x)) for x in (self._n, self._p, self._q)]
		matrices = [repr(x) for x in (self._A, self._B, self._C, self._D)]
		str_mat = """State Space (%d state%s, %d output%s and %d input%s)
		A= %s
		B= %s
		C= %s
		D= %s
		""" % tuple(chain(chain(*size), matrices))

		# Observers Wo, Wc
		# str_mat += tostr( self._Wc, 'Wc')
		# str_mat += tostr( self._Wo, 'Wo')

		# norms
		# str_mat += tostr( self._H2norm, 'H2-norm')
		# str_mat += tostr( self._WCPG, 'WCPG')

		return str_mat


	# ======================================================================================
	def __mul__(self, other):
		"""
		We overload the multiplication operator so that two state spaces in series  give
		a resultant state space with formula checked in matlab and available at :
		https://en.wikibooks.org/wiki/Control_Systems/Block_Diagrams
		To be able to multiply matrixes, systems must respect some constraints
		"""

		n1, p1, q1 = self.size
		n2, p2, q2 = other.size

		if p1 != q2:
			raise ValueError("dSS: second state space should have same number of inputs as first state number of outputs")

		# TODO: possible simplification if self.A==other.A ??

		amul = r_[c_[self.A, self.B*other.C], c_[zeros((n2, n1)), other.A]]
		bmul = r_[self.B*other.D, other.B]
		cmul = c_[self.C, self.D*other.C]
		dmul = self.D*other.D

		return dSS(amul, bmul, cmul, dmul)


	# ======================================================================================
	def __repr__(self):
		"""Returns the representation of the dSS"""
		return str(self)


	def __getitem__(self, *args):
		"""Returns a subsystem"""
		return dSS(self._A, self._B[:, args[0][1]], self._C[args[0][0], :], self._D[args[0][0], args[0][1]])

	def to_dSSmp(self):
		"""Transforms the dSS into a dSSmp (multiprecision dSS)"""
		from fixif.LTI import dSSmp
		return dSSmp(self._A, self._B, self._C, self._D)


	def to_dTF(self):
		"""
		Transform a SISO state-space into a transfer function
		"""
		if self._p != 1 or self._q != 1:
			raise ValueError('dSS: the state-space must be SISO to be converted in transfer function')
		from fixif.LTI import dTF
		num, den = ss2tf(self._A, self._B, self._C, self._D)
		return dTF(num[0], den)

	def simplify(self):
		"""
		This function tries to simplify the state-space msystem.
		It may occur that matrix A contains one or several rows that contain only zeros.
		In this case we have that the corresponding state-space variable depends only on
		the term B[i,:]*u(k):
		x1(k+1) = A[1,:] * x(k) +  B[1,:]*u(k)
		..
		xi(k+1) = B[i,:]*u(k)
		...
		y(k) = C * x(k) + D * u(k)

		Then, we can re-write
		x1(k+1) = A[1,:] * x(k) +  B[1,:]*u(k)
		..
		xi(k+1) = 0
		...
		y(k) = C * x(k) + C[:,i]*(B[i,:]*u(k)) + D * u(k)

		or in matrix form:

			A' is the matrix A with column i and row i deleted
			C' is the matrix C with column i deleted

			then,

			x(k+1) = A' * x(k) + B * u(k)
			y(k)   = C' * x(k) + (D + C[:, i] * B[i,:]) * u(k)

		Returns
		-------

		"""




		newS = self

		while newS.n > numpy.linalg.matrix_rank(newS._A):
			l = list()
			for i in range(0, newS.n):
				if numpy.count_nonzero(newS._A[i, :]) == 0:
					l.append(i)

			A = newS._A
			B = newS._B
			C = newS._C
			D = newS._D


			while len(l) > 0:
				index = l.pop()

				A = numpy.delete(A, index, 1)
				A = numpy.delete(A, index, 0)

				D = D + C[:, index] * B[index, :]

				C = numpy.delete(C, index, 1)

				B = numpy.delete(B, index, 0)


			newS = dSS(A, B, C, D)

			print("number of states: %d \n rank: %d " % (newS.n, numpy.linalg.matrix_rank(newS._A)))

		return newS










	def assert_close(self, other, eps=1e-5):
		"""
		Check if two dSS are almost equal
		Parameters:
		- other: (dSS) the 2nd dSS we want to compare
		- atol: absolute tolerance used for assert_allclose
		"""
		# at this point, it should exist an invertible matrix T such that
		# self.A == inv(T) * other.A * T
		# self.B == inv(T) * other.B
		# self.C == other.C * T
		# self.D == other.D

		# TODO: this is probably not enough...
		# assert_allclose(self.C * self.B, other.C * other.B, rtol=rtol)
		# assert_allclose(self.C * self.A * self.B, other.C * other.A * other.B, rtol=rtol)
		# assert_allclose(self.C * self.A * self.A * self.B, other.C * other.A * other.A * other.B, rtol=rtol)
		# assert_allclose(self.D, other.D, rtol=rtol)
		assert norm(self.C * self.B - other.C * other.B) < eps
		assert norm(self.C * self.A * self.B - other.C * other.A * other.B) < eps
		assert norm(self.C * self.A * self.A * self.B - other.C * other.A * other.A * other.B) < eps
		assert norm(self.D - other.D) < eps



	def balanced(self):
		"""
		Returns an equivalent balanced state-space system

		Use ab09ad method from Slicot to get balanced state-space
		see http://slicot.org/objects/software/shared/doc/AB09AD.html

		Returns
		- a dSS object
		"""
		try:
			Nr, Ar, Br, Cr, hsv = ab09ad('D', 'B', 'N', self.n, self.q, self.p, self.A, self.B, self.C, nr=self.n, tol=1e-18)
		except NameError:
			raise ImportError("dSS.balanced: slycot is not installed")
		if Nr == 0:
			raise ValueError("dSS: balanced: Cannot compute the balanced system "
			                 "(the selected order nr is greater than the order of a minimal realization of the given system)")
		return dSS(Ar, Br, Cr, self.D)



	def __add__(self, S):
		"""
		This method computes the difference between self and a filter S given in the argument such that
		the result filter H := self + S has
					H.A = [[self.A, zeros(self.n, S.n)], [zeros(S.n, self.n), S.A]]
					H.B = [[self.B], [S.B]]
					H.C = [self.C, S.C]
					H.D = [self.D + S.D]
		Parameters:
		- S: a dSS to substract from self

		Returns a dSS which is equal to (self - S)
		"""

		#TODO: check size and raise error

		newA = numpy.concatenate((self.A, numpy.zeros([self.n, S.n])), axis=1)
		tmp = numpy.concatenate((numpy.zeros([S.n, self.n]), S.A), axis=1)
		newA = numpy.concatenate((newA, tmp), axis=0)

		newB = numpy.concatenate((self.B, S.B), axis=0)
		newC = numpy.concatenate((self.C, S.C), axis=1)
		newD = self.D + S.D

		return dSS(newA, newB, newC, newD)



	def __sub__(self, S):
		"""
		This method computes the difference between self and a dSS S given in the argument such that
		the result dSS H := self - S has
			H.A = [[self.A, zeros(self.n, S.n)], [zeros(S.n, self.n), S.A]]
			H.B = [[self.B], [S.B]]
			H.C = [self.C, -S.C]
			H.D = [self.D - S.D]

		Parameters:
		- S: a dSS to substract from self

		Returns a dSS which is equal to (self - S)
		"""

		# TODO: check size and raise error

		newA = numpy.concatenate((self.A, numpy.zeros([self.n, S.n])), axis=1)
		tmp = numpy.concatenate((numpy.zeros([S.n, self.n]), S.A), axis=1)
		newA = numpy.concatenate((newA, tmp), axis=0)

		newB = numpy.concatenate((self.B, S.B), axis=0)
		newC = numpy.concatenate((self.C, -S.C), axis=1)
		newD = self.D - S.D

		return dSS(newA, newB, newC, newD)







def iter_random_dSS(number, stable=True, n=(5, 10), p=(1, 5), q=(1, 5),
                    pRepeat=0.01, pReal=0.5, pBCmask=0.90, pDmask=0.8, pDzero=0.5):
	"""
	Generate some n-th order random (stable or not) state-spaces, with q inputs and p outputs
	copy/Adapted from control-python library (thanks guys): https://sourceforge.net/projects/python-control/
	possibly already adpated from Mathworks or Octave

	Parameters:
		- number: number of state-space to generate
		- stable: indicate if the state-spaces are stable or not
		- n: tuple (mini,maxi) number of states (default:  random between 5 and 10)
		- p: 1 or a tuple (mini,maxi) number of outputs (default: 1)
		- q: 1 or a tuple (mini,maxi) number of inputs (default: 1)

		- pRepeat: Probability of repeating a previous root (default: 0.01)
		- pReal: Probability of choosing a real root (default: 0.5). Note that when choosing a complex root,
		the conjugate gets chosen as well. So the expected proportion of real roots is pReal / (pReal + 2 * (1 - pReal))
		- pBCmask: Probability that an element in B or C will not be masked out (default: 0.9)
		- pDmask: Probability that an element in D will not be masked out (default: 0.8)
		- pDzero: Probability that D = 0 (default: 0.5)

	Returns:
		- returns a generator of dSS objects (to use in a for loop for example)

	..Example::
		>>> sys = list( iter_random_dSS( 12, True, (10,20)) )
		>>> for S in iter_random_dSS( 12, True, (10,20)):
		>>>		print( S )


	"""
	for i in range(number):
		if stable:
			yield random_dSS(randint(*n), randint(*p), randint(*q), pRepeat, pReal, pBCmask, pDmask, pDzero)
		else:
			nn = randint(*n)
			if p == 1 and q == 1:
				pp = 1
				qq = 1
			else:
				pp = randint(*p)
				qq = randint(*q)
			A = mat(rand(nn, nn))
			B = mat(rand(nn, qq))
			C = mat(rand(pp, nn))
			D = mat(rand(pp, qq))


			yield dSS(A, B, C, D)



def random_dSS(n, p, q, pRepeat=0.01, pReal=0.5, pBCmask=0.90, pDmask=0.8, pDzero=0.5):
	"""
	Generate ONE n-th order random  stable state-spaces, with q inputs and p outputs
	copy/adapted from control-python library (Richard Murray): https://sourceforge.net/projects/python-control/
	(thanks guys!)
	possibly already adpated/copied from Mathworks or Octave

	Parameters:
	- n: number of states (default:  random between 5 and 10)
	- p: number of outputs (default: 1)
	- q: number of inputs (default: 1)

	- pRepeat: Probability of repeating a previous root (default: 0.01)
	- pReal: Probability of choosing a real root (default: 0.5). Note that when choosing a complex root,
		the conjugate gets chosen as well. So the expected proportion of real roots is pReal / (pReal + 2 * (1 - pReal))
	- pBCmask: Probability that an element in B or C will not be masked out (default: 0.90)
	- pDmask: Probability that an element in D will not be masked out (default: 0.8)
	- pDzero: Probability that D = 0 (default: 0.5)

	Returns a dSS object
	"""
	# Check for valid input arguments.
	if n < 1 or n % 1:
		raise ValueError("states must be a positive integer.  #states = %g." % n)
	if q < 1 or q % 1:
		raise ValueError("inputs must be a positive integer.  #inputs = %g." % q)
	if p < 1 or p % 1:
		raise ValueError("outputs must be a positive integer.  #outputs = %g." % p)

	# Make some poles for A.  Preallocate a complex array.
	poles = zeros(n) + zeros(n) * 0.j
	i = 0

	while i < n:

		if rand() < pRepeat and i != 0 and i != n - 1:
			# Small chance of copying poles, if we're not at the first or last  element.
			if poles[i - 1].imag == 0:
				poles[i] = poles[i - 1]     # Copy previous real pole.
				i += 1

			else:
				poles[i:i + 2] = poles[i - 2:i]     # Copy previous complex conjugate pair of poles.
				i += 2

		elif rand() < pReal or i == n - 1:
			poles[i] = 2. * rand() - 1.     # No-oscillation pole.
			i += 1

		else:
			mag = rand()    # Complex conjugate pair of oscillating poles.
			phase = 2. * pi * rand()
			poles[i] = complex(mag * cos(phase), mag * sin(phase))
			poles[i + 1] = complex(poles[i].real, -poles[i].imag)
			i += 2

	# Now put the poles in A as real blocks on the diagonal.

	A = zeros((n, n))
	i = 0

	while i < n:

		if poles[i].imag == 0:
			A[i, i] = poles[i].real
			i += 1

		else:
			A[i, i] = A[i + 1, i + 1] = poles[i].real
			A[i, i + 1] = poles[i].imag
			A[i + 1, i] = -poles[i].imag
			i += 2


	while True:     # Finally, apply a transformation so that A is not block-diagonal.
		T = randn(n, n)

		try:
			A = dot(solve(T, A), T)  # A = T \ A * T
			break

		except LinAlgError:
			# In the unlikely event that T is rank-deficient, iterate again.
			pass

	# Make the remaining matrices.
	B = randn(n, q)
	C = randn(p, n)
	D = randn(p, q)

	# Make masks to zero out some of the elements.
	while True:
		Bmask = rand(n, q) < pBCmask
		if not Bmask.all():  # Retry if we get all zeros.
			break

	while True:
		Cmask = rand(p, n) < pBCmask
		if not Cmask.all():  # Retry if we get all zeros.
			break

	if rand() < pDzero:
		Dmask = zeros((p, q))

	else:
		while True:
			Dmask = rand(p, q) < pDmask
			if not Dmask.all():  # Retry if we get all zeros.
				break


	# Apply masks.
	B *= Bmask
	C *= Cmask
	# D *= Dmask

	return dSS(A, B, C, D)

