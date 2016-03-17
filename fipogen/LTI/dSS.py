# coding: utf8

"""
This file contains Object and methods for a Discrete State Space
"""

__author__ = "Thibault Hilaire, Joachim Kruithof"
__copyright__ = "Copyright 2015, FIPOgen Project, LIP6"
__credits__ = ["Thibault Hilaire", "Joachim Kruithof", "Anastasia Lozanova"]

__license__ = "CECILL-C"
__version__ = "0.4"
__maintainer__ = "Thibault Hilaire"
__email__ = "thibault.hilaire@lip6.fr"
__status__ = "Beta"


from numpy					import inf, empty, float64, shape, identity, absolute, dot, eye, array, asfarray, ones  # , astype
from numpy					import matrix as mat, Inf, set_printoptions
from numpy					import eye, zeros, r_, c_, sqrt
from numpy.linalg			import inv, det, solve, eigvals
from numpy.linalg.linalg	import LinAlgError
from scipy.linalg			import solve_discrete_lyapunov
from slycot					import sb03md, ab09ad
from copy					import copy
from scipy.weave			import inline
from scipy.signal import ss2tf

from numpy.testing import assert_allclose


class dSS(object):
	r"""
	The dSS class describes a discrete state space realization

	A state space system :math:`(A,B,C,D)` is defined by

	.. math::

		\left\lbrace \begin{aligned}
		x(k+1) &= Ax(k) + Bu(k) \\
		y(k)   &= Cx(k) + Du(k)
		\end{aligned}\right.

	with :math:`A \in \mathbb{R}^{n \times n}, B \in \mathbb{R}^{n \times q}, C \in \mathbb{R}^{p \times n} \text{ and } D \in \mathbb{R}^{p \times q}`.

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

	_W_method = 'slycot1'  # linalg, slycot1


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
		self._H2norm = None    # keep ?
		self._DC_gain = None    # keep ?
		self._WCPG = None


	# Properties
	@property
	def A(self):
		return self._A

	@property
	def B(self):
		return self._B

	@property
	def C(self):
		return self._C

	@property
	def D(self):
		return self._D

	@property
	def n(self):
		return self._n

	@property
	def p(self):
		return self._p

	@property
	def q(self):
		return self._q

	# Wc and Wo are computed only once
	@property
	def Wo(self):
		if (self._Wo is None):
			self.calc_Wo()
		return self._Wo

	@property
	def Wc(self):
		if (self._Wc is None):
			self.calc_Wc()
		return self._Wc

	@property
	def size(self):
		"""
		Return size of state space
		"""
		return (self._n, self._p, self._q)


	#======================================================================================#
	# Observers (Wo, Wc) calculation
	#======================================================================================#
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

		- ``slycot1`` : using ``slycot`` lib with func ``sb03md``, like in [matlab ,pydare]
		see http://slicot.org/objects/software/shared/libindex.html

		- ``None`` (default) : use the default method defined in the dSS class (dSS._W_method)

		..Example::

			>>>mydSS = random_dSS() ## define a new state space from random data
			>>>mydSS.calc_Wo('linalg') # use numpy
			>>>mydSS.calc_Wo('slycot1') # use slycot
			>>>mydSS.calc_Wo() # use the default method defined in dSS

		.. warning::

			solve_discrete_lyapunov does not work as intended, see http://stackoverflow.com/questions/16315645/am-i-using-scipy-linalg-solve-discrete-lyapunov-correctl
			Precision is not good (4 digits, failed tests)

		"""

		if method is None:
			method = dSS._W_method

		if (method == 'linalg'):
			try:
				X = solve_discrete_lyapunov(self._A.transpose(), self._C.transpose() * self._C)
				self._Wo = mat(X)

			except LinAlgError as ve:
				if (ve.info < 0):
					e = LinAlgError(ve.message)
					e.info = ve.info
				else:
					e = LinAlgError( "dSS: Wo: scipy Linalg failed to compute eigenvalues of Lyapunov equation")
					e.info = ve.info
				raise e

		elif (self._W_method == 'slycot1'):
			# Solve the Lyapunov equation by calling the Slycot function sb03md
			# If we don't use "copy" in the call, the result is plain false

			try:
				X, scale, sep, ferr, w = sb03md(self.n, -self._C.transpose() * self._C, copy(self._A.transpose()), eye(self.n, self.n), dico='D', trana='T')
				self._Wo = mat(X)

			except ValueError as ve:

				if ve.info < 0:
					e = ValueError(ve.message)
					e.info = ve.info
				else:
					e = ValueError("dSS: Wo: The QR algorithm failed to compute all the eigenvalues (see LAPACK Library routine DGEES).")
					e.info = ve.info
				raise e

		else:
			raise ValueError("dSS: Unknown method to calculate observers (method=%s)"%method)


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

		- ``slycot1`` : using ``slycot`` lib with func ``sb03md``, like in [matlab ,pydare]
		see http://slicot.org/objects/software/shared/libindex.html

		- ``None`` (default) : use the default method defined in the dSS class (dSS._W_method)

		..Example::

			>>>mydSS = random_dSS() ## define a new state space from random data
			>>>mydSS.calc_Wc('linalg') # use numpy
			>>>mydSS.calc_Wc('slycot1') # use slycot
			>>>mydSS.calc_Wo() # use the default method defined in dSS

		.. warning::

			solve_discrete_lyapunov does not work as intended, see http://stackoverflow.com/questions/16315645/am-i-using-scipy-linalg-solve-discrete-lyapunov-correctl
			Precision is not good (4 digits, failed tests)

		"""
		if method is None:
			method = dSS._W_method

		if (method == 'linalg'):
			try:
				X = solve_discrete_lyapunov(self._A, self._B * self._B.transpose())
				self._Wc = mat(X)

			except LinAlgError as ve:
				if (ve.info < 0):
					e = LinAlgError(ve.message)
					e.info = ve.info
				else:
					e = LinAlgError( "dSS: Wc: scipy Linalg failed to compute eigenvalues of Lyapunov equation")
					e.info = ve.info
				raise e

		elif (self._W_method == 'slycot1'):
			# Solve the Lyapunov equation by calling the Slycot function sb03md
			# If we don't use "copy" in the call, the result is plain false

			try:
				X, scale, sep, ferr, w = sb03md(self.n, -self._B * self._B.transpose(), copy(self._A), eye(self.n, self.n), dico='D', trana='T')
				self._Wc = mat(X)

			except ValueError as ve:

				if ve.info < 0:
					e = ValueError(ve.message)
					e.info = ve.info
				else:
					e = ValueError("dSS: Wc: The QR algorithm failed to compute all the eigenvalues (see LAPACK Library routine DGEES).")
					e.info = ve.info
				raise e

		else:
			raise ValueError("dSS: Unknown method to calculate observers (method=%s)"%method)


	#======================================================================================#
	# Norms calculation
	#======================================================================================#

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
			self._H2norm = sqrt(M.trace())
		except:
			try:
				M = self._B.transpose() * self.Wo * self._B + self._D * self._D.transpose()
				self._H2norm = sqrt(M.trace())
			except:
				raise ValueError( "dSS: h2-norm : Impossible to compute M. Default value is 'inf'" )

		return self._H2norm






	#======================================================================================#
	def WCPG(self):

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
				A = array(self._A)
				B = array(self._B)
				C = array(self._C)
				D = array(self._D)
				n,p,q = self.size
				W = empty( (p, q), dtype=float64)

				code = "return_val = WCPG_ABCD( &W[0,0], &A[0,0], &B[0,0], &C[0,0], &D[0,0], n, p, q);"
				support_code = 'extern "C" int WCPG_ABCD(double *W, double *A, double *B, double *C, double *D, uint64_t n, uint64_t p, uint64_t q);'
				err = inline(code, ['W', 'A', 'B', 'C', 'D', 'n', 'p', 'q'], support_code=support_code, libraries=["WCPG"])
				if err==0:
					# change numpy display formatter, so that we can display the full coefficient in hex (equivalent to printf("%a",...) in C)
					set_printoptions(formatter={'float_kind':lambda x:x.hex()})
					print(self)
					raise ValueError( "WCPG: cannot compute WCPG")
				self._WCPG = W
			except:
				raise ValueError( "dSS: Impossible to compute WCPG matrix. Is WCPG library really installed ?")

		return self._WCPG


	#======================================================================================#
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
			except:
				raise ValueError( 'dSS: Impossible to compute DC-gain from current discrete state space' )

		return self._DC_gain


	#======================================================================================#
	def _check_dimensions( self ):
		"""
		Computes the number of inputs and outputs.
		Check for concordance of the matrices' size
		"""

		# A
		a1, a2 = self._A.shape
		if a1 != a2:
			raise ValueError( 'dSS: A is not a square matrix' )
		n = a1

		# B
		b1, b2 = self._B.shape
		if b1 != n:
			raise ValueError( 'dSS: A and B should have the same number of rows' )
		inputs = b2

		# C
		c1, c2 = self._C.shape
		if c2 != n:
			raise ValueError( 'dSS: A and C should have the same number of columns')
		outputs = c1

		# D
		d1, d2 = self._D.shape
		if (d1 != outputs or d2 != inputs):
			raise ValueError( 'dSS: D should be consistent with C and B' )

		return n, outputs, inputs


	#======================================================================================#
	def __str__(self):
		"""
		Display the state-space
		"""

		def tostr(M, name):
			if M is not None:
				return name + "= " + repr(M) + "\n"
			else:
				return name + " is not computed\n"

		def plural(n):
			return 's' if n>0 else ''

		str_mat = """State Space (%d state%s, %d output%s and %d input%s)
		A= %s
		B= %s
		C= %s
		D= %s
		"""% (self._n, plural(self._n), self._p, plural(self._p), self._q, plural(self._q), repr(self._A), repr(self._B), repr(self._C), repr(self._D) )

		# Observers Wo, Wc
		#str_mat += tostr( self._Wc, 'Wc')
		#str_mat += tostr( self._Wo, 'Wo')

		# norms
		#str_mat += tostr( self._H2norm, 'H2-norm')
		#str_mat += tostr( self._WCPG, 'WCPG')

		return str_mat


	#======================================================================================#
	def __mul__(self, other):
		"""
		We overload the multiplication operator so that two state spaces in series  give
		a resultant state space with formula checked in matlab and available at :
		https://en.wikibooks.org/wiki/Control_Systems/Block_Diagrams
		To be able to multiply matrixes, systems must respect some constraints
		"""

		# TODO: we must verify the following conditions for matrix multiplication
		# n2 = n1
		# p2 = q1
		# q2 = p1
		# p2 = n1 (=> n2 = p2)
		# n2 = q1 (=> id)

		n1, p1, q1 = self.size
		n2, p2, q2 = other.size

		if (not(n1 == n2)):
			raise ValueError( "dSS: States spaces must have same number of states n")
		elif (not(p1 == n2)):
			raise ValueError( "dSS: second state space should have same number of states as first state number of inputs")
		elif (not(n1 == q2)):
			raise ValueError( "dSS: second state space should have same number of outputs as first state number of states")
		elif (not(p1 == q2)):
			raise ValueError( "dSS: second state space should have number of outputs equal to first state space number of inputs")
		elif (not(q1 == p2)):
			raise ValueError( "dSS: second state space number of inputs should be equal to first state space number of outputs")

		#TODO: possible simplification if self.A==other.A ??

		amul = r_[c_[ self.A, self.B*other.C ], c_[ zeros((n2, n1)), other.A ]]
		bmul = r_[ self.B*other.D, other.B ]
		cmul = c_[ self.C, self.D*other.C ]
		dmul = self.D*other.D

		return dSS(amul, bmul, cmul, dmul)


	#======================================================================================#
	def __repr__(self):
		return str(self)


	# get subsystem
	def __getitem__(self, *args):

		return dSS(self._A, self._B[:,args[0][1]], self._C[args[0][0],:], self._D[args[0][0],args[0][1]])


	def to_dTF(self):
		"""
		Transform a SISO state-space into a transfer function

		"""
		if self._p!=1 or self._q!= 1:
			raise ValueError( 'dSS: the state-space must be SISO to be converted in transfer function')
		from fipogen.LTI import dTF
		num,den = ss2tf( self._A, self._B, self._C, self._D)
		return dTF( num[0], den )


	def assert_close(self, other):
		# at this point, it should exist an invertible matrix T such that
		# self.A == inv(T) * other.A * T
		# self.B == inv(T) * other.B
		# self.C == other.C * T
		# self.D == other.D

		#TODO: this is probably not enough...
		assert_allclose( self.C*self.B, other.C*other.B, atol=1e-12)
		assert_allclose( self.C*self.A*self.B, other.C*other.A*other.B, atol=1e-12)
		assert_allclose( self.C*self.A*self.A*self.B, other.C*other.A*other.A*other.B, atol=1e-12)
		assert_allclose( self.D, other.D, atol=1e-12)


	def balanced(self):
		"""
		Returns an equivalent balanced state-space system

		Use ab09ad method from Slicot to get balanced state-space
		see http://slicot.org/objects/software/shared/doc/AB09AD.html

		Returns
		- a dSS object
		"""

		Nr, Ar, Br, Cr, hsv = ab09ad( 'D', 'B', 'N', self.n, self.q, self.p, self.A, self.B, self.C, nr= self.n, tol=0.0)
		if Nr==0:
			raise ValueError("dSS: balanced: The selected order nr is greater than the order of a minimal realization of the given system. It was set automatically to a value corresponding to the order of a minimal realization of the system")
		return dSS( Ar, Br, Cr, self.D)