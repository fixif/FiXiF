#coding: UTF8

"""
This file contains State-Space structure

"""

__author__ = "Thibault Hilaire, Joachim Kruithof"
__copyright__ = "Copyright 2015, FIPOgen Project, LIP6"
__credits__ = ["Thibault Hilaire", "Joachim Kruithof"]

__license__ = "CECILL-C"
__version__ = "0.4"
__maintainer__ = "Thibault Hilaire"
__email__ = "thibault.hilaire@lip6.fr"
__status__ = "Beta"


from fipogen.Structures import Structure
from numpy import eye, zeros



def makeSS( filter, form=None ):
	"""
	Factory function to make a Direct Form II Realization

	One option:
	- transposed: (boolean) indicates if the realization is transposed (Direct Form II or Direct Form II transposed)

	Returns
	- a dictionary of necessary infos to build the Realization
	"""

	if form==None:
		S = filter.dSS
	elif form=='balanced':
		S = filter.dSS.balanced()
	elif form=='ctrl' or form=='obs':
		S = filter.dTF.to_dSS(form)
	else:
		raise ValueError("State-Space: the form '%s' is invalid. Must be in (None, 'balanced', 'ctrl', 'obs')"%form)

	n,p,q = S.size
	l = 0
	JtoS = ( eye((l)), zeros((n,l)), zeros((p,l)), zeros((l,n)), zeros((l,q)), S.A, S.B, S.C, S.D )

	return {"JtoS": JtoS}



def acceptSS(filter, form):
	"""
	The forms 'ctrl' and 'obs' cannot be applied for SISO filters
	'balanced' form is for stable filter
	otherwise, it can always be used
	"""
	if form=='balanced':
		return filter.isStable()
	if form=='ctrl' or form=='obs':
		return filter.isSISO()

	# otherwise
	return True



State_Space = Structure( shortName="SS", fullName="State-Space", options={ 'form': (None, 'balanced', 'ctrl', 'obs')}, make=makeSS, accept=acceptSS)
