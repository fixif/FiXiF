#coding=utf8

from fipogen.SIF import SIF
from fipogen.Structures.Structure import Structure

from numpy import matrix as mat
from numpy import diagflat, zeros, eye, rot90, ones, r_, c_, atleast_2d
from numpy.linalg import inv

class DFI(Structure):

	_name = "Direct Form I"              # name of the structure
	_possibleOptions = { "nbSum" : (1,2) }       # the only option is nbSum, that can be 1 or 2
	_acceptMIMO = False

	def __init__(self, filter, nbSum=1):
		"""
		Two options are available

		nbSum=1 - compute \sum b_i u(k-i) and \sum a_i y(k-i) in the same Sum-of-Products
		nbSum=2 - compute \sum b_i u(k-i) and \sum a_i y(k-i) in two Sums-of-Products

		"""

		# check the args
		self.manageOptions(nbSum=nbSum)

		# convert everything to mat
		n = filter.dTF.order
		num = mat(filter.dTF.num)
		den = mat(filter.dTF.den)

		# Compute J to S matrices

		P = mat( r_[c_[ diagflat(ones((1, n-1)), -1), zeros((n, n))],c_[zeros((n, n)), diagflat(ones((1, n-1)), -1) ]] )
		Q = mat( r_[ atleast_2d(1), zeros((2*n-1, 1)) ] )
		R = mat( zeros( (1,2*n) ) )
		S = mat( atleast_2d(0) )

		if nbSum == 1:
			J = mat( atleast_2d(1) )
			K = mat( r_[ zeros( (n,1) ), atleast_2d(1), zeros( (n-1,1) ) ] )
			L = mat( atleast_2d(1) )
			M = mat( c_[ num[0,1:], -den[0,1:] ] )
			N = atleast_2d(num[0,0])
		else:
			J = mat( [[1,0],[-1,1]])
			K = c_[ zeros((2*n,1)), r_[ zeros((n,1)), atleast_2d(1), zeros((n-1, 1)) ]]
			L = mat( [[0, 1]])
			M = r_[  c_[ num[0,1:], zeros((1,n))], c_[ zeros((1,n)), -den[0,1:]]  ]
			N = mat( [ [num[0,0]], [0] ])


	# transformation to 'optimize' the code

		# T = mat(rot90(eye(2*nnum)))
		#
		# invT = inv(T)
		#
		# # build SIF
		#
		# if opt == 1:
		#
		# 	JtoS = atleast_2d(den[0,0]), invT*gamma4, atleast_2d(1), gamma1*T, atleast_2d(num[0,0]), invT*gamma2*T, invT*gamma3, mat(zeros((1, nnum+nden))), atleast_2d(0)
		#
		# elif opt == 2:
		#
		# 	JtoS = mat(eye(2)), invT*gamma4, mat([1,1]), gamma1*T, r_[atleast_2d(num[0,0]),atleast_2d(0)], invT*gamma2*T, invT*gamma3, mat(zeros((1, nnum+nden))), atleast_2d(0)

		# build SIF
		self.SIF = SIF( (J, K, L, M, N, P, Q, R, S) )


