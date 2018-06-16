# coding: utf8

"""
This file contains Lattice Wave Digital Filter

"""

__author__ = "Thibault Hilaire, Anastasia Volkova"
__copyright__ = "Copyright 2015, FiXiF Project, LIP6"
__credits__ = ["Thibault Hilaire", "Anastasia Volkova"]

__license__ = "GPL v3"
__version__ = "0.4"
__maintainer__ = "Thibault Hilaire"
__email__ = "thibault.hilaire@lip6.fr"
__status__ = "Beta"

import os
from fixif.Structures.Structure import Structure
from numpy import matrix as mat
# from matlab.engine import connect_matlab
from fixif.func_aux import MatlabHelper

try:
	import matlab


	def makeLWDF(filt):
		"""

		"""
		# connect to matlab if not already connected
		try:
			MH = MatlabHelper()
			eng = MH.engine

			# TODO: correct this shit !
			# we suppose that we start in the root of the git repository, i.e. at yourlocalpath/fipogen
			p = os.getcwd() + '/construct/fwrtoolbox/FWRToolbox/'
			eng.cd(p)

			# eng.addpath('construct', 'fwrtoolbox')
			# eng.eval('R=ButterLWDF2FWR( %d, %f);'%(filter.n, filter.Wn), nargout=0)

			# eng.eval('R=TF2LWDF2SIF( %f, %f);' % (filter.dTF.num.tolist(), filter.dTF.den.tolist()), nargout=0)
			# R = eng.eval('struct(R)')

			R = eng.TF2LWDF2SIF(matlab.double(filt.dTF.num.tolist()), matlab.double(filt.dTF.den.tolist()))
		except: 	# TODO: catch the right error
			raise ValueError('Could not create the LWDF structure using matlab.\n')

		# build SIF
		return {"JtoS": (
			mat(R['J']), mat(R['K']), mat(R['L']), mat(R['M']), mat(R['N']), mat(R['P']), mat(R['Q']), mat(R['R']),
			mat(R['S']))}


	def acceptLWDF(filt):
		"""
		a LWDF realization can be build only if the filter is SISO and has EVEN order
		"""
		return (filt.order % 2 == 1) and filt.isSISO()


	LWDF = Structure(shortName='LWDF', fullName="Lattice Wave Digital Filter", make=makeLWDF, accept=acceptLWDF)

except ImportError:
	# matlab Python engine is not installed
	pass
