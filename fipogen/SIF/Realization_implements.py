#coding=UTF8

__author__ = "Thibault Hilaire, Joachim Kruithof"
__copyright__ = "Copyright 2015, FIPOgen Project, LIP6"
__credits__ = ["Thibault Hilaire", "Joachim Kruithof"]

__license__ = "CECILL-C"
__version__ = "0.4"
__maintainer__ = "Thibault Hilaire"
__email__ = "thibault.hilaire@lip6.fr"
__status__ = "Beta"


from jinja2 import Environment, PackageLoader
from numpy import tril, all
from datetime import datetime
from fipogen.func_aux import scalarProduct

from numpy import matrix as mat, zeros,eye, empty, float64
from scipy.weave import inline

import os
from subprocess import call


GENERATED_PATH = 'generated/code/'



# list of methods to be added to the Realization class
__all__ = ["implementCdouble", "runCdouble"]



def genCvarNames(baseName, nbVar):
	"""
	Generate a list of C-language variable name, based on the basedName and the number of variable
	genCvarNames( 'u', nbVar) returns:
	- 'u' if nbVar == 1
	- otherwise [ 'u_1', 'u_2', ..., 'u_n' ]
	"""
	if nbVar == 1:
		return [ baseName ]
	else:
		return [ baseName+"[%d]"%i for i in range(nbVar) ]



def implementCdouble(self, funcName):
	"""
	Returns (as a tuple of two strings) the C-code (with double coefficients) correspoding to the SIF self AND the C-code calling this function
	The C code is generated from the template `algorithmC_template.c` in the folder directory

	Parameters:
		- self: the SIF object
		- funcName: name of the function
		- commentName: name of the SIF to be added in the comment (the name of the structure ?)
	"""

	env = Environment( loader=PackageLoader('fipogen','SIF/templates'), trim_blocks=True, lstrip_blocks=True )
	cTemplate = env.get_template('algorithmC_template.c')

	cDict = {}	# dictionary used to fill the template
	cDict['funcName'] = funcName
	if self._filter.isSISO():
		cDict['SIFname'] = self.name + '\n' + str(self._filter.dTF)
	else:
		cDict['SIFname'] = self.name + '\n' + str(self._filter.dSS)
	cDict['date'] = datetime.now().strftime("%Y/%m/%d - %H:%M:%S")

	l,n,p,q = self.size

	# Lower triangular part non-null ?
	# in that case, we can directly store the computation of x(k+1) in x(k)
	# (no need to first compute x(k+1), and then store x(k+1) in x(k) to prepare the next step)
	isPlt = all(tril(self.P, -1) == 0)

	# input(s), output(s), states, intermediate variables
	strU = genCvarNames('u', q)
	strY = genCvarNames('y', p)
	strXk = genCvarNames('xk', n)
	strXkp = [ 'x%d_kp1'%(i) for i in range(n) ]
	strT = 	[ 'T%d'%(i) for i in range(l) ]

	strTXU = strT + strXk + strU

	if isPlt:
		strTXY = strT + strXk + strY
	else:
		strTXY = strT + strXkp + strY

	# define the input/output variables in the signature of the function
	signature = []
	if p == 1:
		cDict['OutVar'] = 'double'
	else:
		cDict['OutVar'] = 'void'
		signature.append('double* y')

	if q == 1:
		signature.append( 'double u')
	else:
		signature.append( 'double* u')

	signature.append( 'double* xk')
	cDict['InVar'] = ', '.join(signature)

	# declare the output variable if necessary, and all the intermediate variables
	cDict['ExtraVar'] = ''
	if not isPlt:
		cDict['ExtraVar'] += '\tdouble ' + ", ".join(strXkp) + ";\n"
	if p == 1:
		cDict['ExtraVar'] += '\tdouble y;'


	# do all the computations
	# intermediate variables J.t = M.x(k) + N.u(k)
	# states x(k+1) =  K.t + P.x(k) + Q.u(k)
	# and outputs y(k) = L.t + R.x(k) + S.u(k)
	comp = []
	for i in range(0, l+n+p):
		comp.append( "\t" + strTXY[i] + " = " + scalarProduct( strTXU, self.Zcomp[i,:], self.dZ[i,:] ) + ";\n" )
	cDict["InterComp"] = "".join( "\tdouble "+ t for t in comp[0:l] )
	cDict["StatesComp"] = "".join( comp[l:l+n] )
	cDict["OutComp"] = "".join( comp[l+n:] )

	# if l>0:
	# 	cDict["InterComp"] += 'printf("T=' + "%a, "*l + '\\n",' + ", ".join(strT) + ');\n'
	# cDict["StatesComp"] += 'printf("X=' + "%a, "*n + '\\n",' + ", ".join(strXk) + ');\n'
	# cDict["OutComp"] += 'printf("Y=' + "%a, " * p + '\\n",' + ", ".join(strY) + ');\n' + 'printf("U=' + "%a, " * q + '\\n",' + ", ".join(strU) + ');'


	# permutation
	cDict['Permutations'] = ""

	if not isPlt:
		cDict['Permutations'] += "\t//permutations\n"
		for i in range(n):
			cDict['Permutations'] +=  "\t" + strXk[i] + " = " + strXkp[i] + ";\n"

	if p==1:
		cDict['return'] = "\treturn y;"

	funcCode = cTemplate.render(**cDict)




	pu_str = '*pu' if self.q == 1 else 'pu'
	if self.p == 1:
		iteration = "*py = %s( %s, xk);" % (funcName,pu_str)
	else:
		iteration = "%s( py, %s, xk);" % (funcName,pu_str)
	callingCode = """
	double xk[%d]={0};
	double *pu = u;
	double *py = yC;
	for( int i=0; i<N; i++)
	{
		%s
		pu += %d;
		py += %d;
	}
	""" % (self.n, iteration, self.q, self.p)


	return funcCode, callingCode


def runCdouble(self, u, fileName='runCdouble'):
	"""
	Generates C code with double, compile it, and run it with the given input u
	Parameters
	----------
	self: the SIF object
	u: the input (qxN), where N is the number of samples
	Returns:
		the ouput (pxN)
	"""
	#u=mat(u, dtype=float64)
	#u = zeros( u.shape, dtype=float64)
	N = u.shape[1]
	yC = zeros( (N,self.p), dtype=float64)  # empty output to be computed by the `implementCdouble` code

	func,run_code = self.implementCdouble(fileName)
	inline(run_code, ['N', 'u', 'yC'], support_code=func, verbose=1, force=1)

	return yC.transpose()
