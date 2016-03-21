# coding: utf8

"""
This file contains Object and methods for a structure


To Build a structure, we should
- build a class derived from Structure class
- set the name (_name)
- set the options (dictionary _possibleOptions)
- if the structure cannot handle some filters (MIMO filters, for example), override the canAcceptFilter method
- in the constructor:
  - run manageOptions (that check if the options are correct, and store the options of the instance)
  - set the SIF (_SIF)

"""

__author__ = "Thibault Hilaire"
__copyright__ = "Copyright 2015, FIPOgen Project, LIP6"
__credits__ = ["Thibault Hilaire", "Chevrel Philippe"]

__license__ = "CECILL-C"
__version__ = "0.4"
__maintainer__ = "Thibault Hilaire"
__email__ = "thibault.hilaire@lip6.fr"
__status__ = "Beta"

import os
from glob import glob
import imp
from itertools import izip, product

class Structure(object):
	"""
	- name: name of the structure
	"""

	_possibleOptions = None         # dictionary of options and their possible values (ex. { 'isScaled': (True,False) })
									#   key: name of the option
									#   value: list of possible values
	_name = ""                      # name of the structures



	def __str__(self):
		"""
		Return string describing the structured SIF
		"""
		return "Structured realization (" + self.fullName + ")\n" + str(self.SIF)


	@property
	def name(self):
		return self._name

	@property
	def fullName(self):
		return self._name + " (" + ", ".join( '%s:%s'%(key,str(val)) for key,val in self._options.items() ) + ")"


	@staticmethod
	def canAcceptFilter(filter, **options):
		"""
		Each structure should redefine this method
		It returns True if the structure can be applied for that filter and these options
		(for example, some structures can be applied for SISO filters, or stable filters, or even, depending on the options, it can or it cannot)
		"""
		return True


	def manageOptions(self, **options):
		"""
		Check the options and store them
		"""
		self._options = options
		for opt,val in options.items():
			if self._possibleOptions is None:
				raise ValueError( self.__class__.__name__ + ": the option " + opt + "=" + str(val) + " is not correct")
			if opt not in self._possibleOptions:
				raise ValueError( self.__class__.__name__ + ": the input argument " + opt + " doesn't exist")
			if val not in self._possibleOptions[opt]:
				raise ValueError( self.__class__.__name__ + ": the option " + opt + "=" + str(val) + " is not correct")


	@property
	def SIF(self):
		return self._SIF


def iterStructures(lti):
	"""
	Iterate over all the possible structures, to build (and return through a generator) all the possible realization
	of a given LTI filter (lti)
	Parameters
	----------
	- lti: the filter (LTI object) we want to implement

	Returns
	-------
	a generator

	>>>> f = LTI( num=[1, 2, 3, 4], den=[5.0,6.0,7.0, 8.0])
	>>>> for R in Structure.iterStructures(f):
	>>>>    print(R)

	print the filter f implemeted in all the existing structures wih all the possible options
	(ie Direct Form I (with nbSum=1 and also nbSum=2), State-Space (balanced, canonical observable form, canonical controlable, etc.), etc.)

	"""
	for cls in Structure.__subclasses__():
		if cls._possibleOptions:
			# list of all the possible values for dictionnary
			# see http://stackoverflow.com/questions/5228158/cartesian-product-of-a-dictionary-of-lists
			vl = ( dict(izip(cls._possibleOptions, x)) for x in product(*cls._possibleOptions.itervalues()) )
			for options in vl:
				if cls.canAcceptFilter(lti, **options):
					yield cls(lti, **options)
		else:
			if cls.canAcceptFilter(lti):
				yield cls(lti)