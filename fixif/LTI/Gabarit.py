# coding: utf8

"""
This file contains the class Gabarit for a freq. specification
"""

__author__ = "Thibault Hilaire"
__copyright__ = "Copyright 2015, FiXiF Project, LIP6"
__credits__ = ["Thibault Hilaire"]

__license__ = "GPL v3"
__version__ = "0.4"
__maintainer__ = "Thibault Hilaire"
__email__ = "thibault.hilaire@lip6.fr"
__status__ = "Beta"


from fixif.LTI import dTF
from fixif.func_aux import MatlabHelper, isMatlabInstalled

from scipy.signal import iirdesign, freqz
from numpy import array, pi, log10, infty
from numpy.random import seed as set_seed, choice, randint, uniform

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# try to install sollya
try:
	import sollya
except ImportError:
	pass


class Band(object):
	"""A band is a zone in frequency (between two frequencies in Hz), with a gain in an interval or lower than a value
	It could be a pass band (gain in [G1;G2]) or astop band (gain<G)
	Gains are in dB, frequencies in Hz (except if Fs is None, otherwise frequencies are Nyquist normalised frequencies)
	"""

	def __init__(self, Fs, F1, F2, Gain):
		"""
		Constructor of a band (a pass band or a stop band)
		Parameters:
		- Fs: sampling Frequency (Hz), None if unspecified
			(then the frequencies are Nyquist normalised frquencies, between 0 and 1)
		- F1,F2: frequencies of the band (F2 can be None, to indicate F2 = Fs/2)
		- Gain: Gain (in dB) of the band -> negative for attenuation !!
			CONVENTION: a 2-tuple for pass Band, or a float for stop Band
		"""
		self._Fs = Fs if Fs else 2
		self._F1 = F1
		self._F2 = F2
		if isinstance(Gain, (tuple, list)):
			# pass band (the gains are sorted)
			self._stopGain = None
			self._passGains = (Gain[0], Gain[1]) if Gain[0] < Gain[1] else (Gain[1], Gain[0])
		else:
			# stop band
			self._stopGain = Gain
			self._passGains = None

	@property
	def Fs(self):
		return self._Fs

	@property
	def F1(self):
		return self._F1

	@property
	def F2(self):
		return self._F2 if self._F2 else float(self._Fs/2)

	@property
	def w1(self):
		"""Normalized frequency (approx. due to the division)"""
		return 2*float(self._F1)/self._Fs

	@property
	def w2(self):
		"""Normalized frequency (approx. due to the division)"""
		return 2*float(self._F2)/self._Fs if self._F2 else 1

	@property
	def passGains(self):
		return self._passGains

	@property
	def stopGain(self):
		return self._stopGain

	@property
	def isPassBand(self):
		"""is the band a pass band ?"""
		return bool(self._passGains)        # True if not None or 0

	def __lt__(self, other):
		"""compare two bands"""
		return self.F1 < other.F1

	def __sub__(self, other):
		"""Substract a Band and a Gain"""
		try:
			stopGain = self._stopGain-other if self._stopGain else None
			passGains = (self._passGains[0]-other, self._passGains[1]-other) if self._passGains else None
		except Exception:
			raise ValueError("The gain should be a constant")
		return Band(self._Fs, self._F1, self._F2, passGains or stopGain)

	def __repr__(self):
		return "Band(%s,%s,%s,stopGain=%s,passGains=%s)" % (self.Fs, self.F1, self.F2, self._stopGain, self._passGains)

	def __str__(self):
		if self.isPassBand:
			return "Freq. [%sHz,%sHz]: Passband in [%sdB, %sdB]" % (self.F1, self.F2, self._passGains[0], self._passGains[1])
		else:
			return "Freq. [%sHz,%sHz]: Stopband at %sdB" % (self.F1, self.F2, self._stopGain)

	def sollyaConstraint(self, margin):
		"""
		Parameter:
		- margin: margin we add to the band (not in dB)
			margin is negative when the band is reduced
		Returns a dictonary for sollya checkModulusFilterInSpecification
		"""
		# deal with Sollya
		Gabarit.readyToRunWithSollya()

		w1 = 2*sollya.SollyaObject(self._F1)/self._Fs
		w2 = 2*sollya.SollyaObject(self._F2)/self._Fs if self._F2 else 1    # F2==None -> F2=Fs/2, so w2=1
		margin = sollya.SollyaObject(margin)

		if self.isPassBand:
			# pass band
			betaInf = 10 ** (sollya.SollyaObject(self._passGains[0]) / 20) - margin
			betaSup = 10 ** (sollya.SollyaObject(self._passGains[1]) / 20) + margin
		else:
			# stop band
			betaInf = 0
			betaSup = 10 ** (sollya.SollyaObject(self._stopGain) / 20) + margin

		assert(betaInf < betaSup)

		return {"Omega": sollya.Interval(w1, w2), "omegaFactor": sollya.pi, "betaInf": sollya.round(betaInf, 53, sollya.RU), "betaSup": sollya.round(betaSup, 53, sollya.RD)}

	def Rectangle(self, dB, minG=-200):
		"""
		Returns a rectangle object, to be used with matplotlib
		The rectangle corresponds to the (stop/pass) band to draw on a Bode diagram
		Parameters:
		- dB: (boolean) True if the scale is logarithmic (dB)
		- minG: minimum y-value for the plot
		"""
		if dB:
			if self.isPassBand:
				return Rectangle((self.F1, self.passGains[0]), (self.F2 - self.F1), self.passGains[1] - self.passGains[0], facecolor="red", alpha=0.3)
			else:
				return Rectangle((self.F1, self.stopGain), self.F2 - self.F1, minG, facecolor="red", alpha=0.3)
		else:
			if self.isPassBand:
				return Rectangle((self.F1, 10**(self.passGains[0]/20.0)), (self.F2 - self.F1), 10**(self.passGains[1]/20.0) - 10**(self.passGains[0]/20.0), facecolor="red", alpha=0.3)
			else:
				return Rectangle((self.F1, 10**(self.stopGain/20.0)), self.F2 - self.F1, -10**(self.stopGain/20.0), facecolor="red", alpha=0.3)


	def applyDesignMargin(self, margin):
		"""
		change the band according to the margin (in dB)
		(positive when we reduce the band)
		"""
		if self.isPassBand:
			self._passGains = self._passGains[0] + margin, self._passGains[1] - margin
		else:
			self._stopGain -= margin



class Gabarit(object):
	"""
	A Gabarit object represents a freq. specification
	It is decomposed in bands, that can be pass-band (amplitude in [x;y]) or stop-band (amplitude less than z)
	"""
	isSollyaRunning = None		# None (untested), True or False

	@staticmethod
	def readyToRunWithSollya():
		"""load gabarit.sol and check if ready/ok"""

		if not Gabarit.isSollyaRunning:
			Gabarit.isSollyaRunning = True
			try:
				sollya.suppressmessage(57, 174, 130, 457)
				sollya.execute("fixif/LTI/gabarit.sol")
			except NameError:
				raise ValueError("Sollya and SollyaPython are not installed !")




	def __init__(self, Fs, Fbands, Abands, seed=None):
		"""
		Build a Gabarit, from list of bands, and list of amplitudes (in dB)
		Parameters:
		----------
		- Fs: (float) sampling frequency (set to None or .5 if the Frequency are Nyquist frequencies, between 0 and 1)
		- Fbands: list of bands (a band is a tuple (F1,F2); F2 may be None to indicates that it is the end of the band (=Fs/2))
		- Abands: list of amplitudes (in dB)
				for pass band, the amplitude is a tuple (x,y) --> the amplitude must be between x dB and y dB
				for stop band, the amplitude is a float x --> the amplitude must be lower than x dB
		- seed: seed used to generate it (not used, just stored for the record)
		"""
		# sampling frequency
		self._Fs = Fs

		if len(Fbands) != len(Abands):
			raise ValueError("Fbands and Abands should be lists/tuples with same size")

		# store the bands (sorted)
		self._bands = [Band(Fs, F1, F2, G) for (F1, F2), G in zip(Fbands, Abands)]
		self._bands.sort()

		self._type = None
		self._seed = seed

	def __str__(self):
		seed = "Seed=%s\n" % (self._seed,) if self._seed else ""
		return "%sType: %s (Fs=%sHz)\n%s" % (seed, self.type, self._Fs, "\n".join(str(b) for b in self._bands))

	@property
	def seed(self):
		return self._seed

	def maxGain(self):
		"""Compute the maximum gain of the gabarit in dB
		"""
		return max(b.passGains[1] if b.isPassBand else b.stopGain for b in self._bands)

	@property
	def type(self):
		"""
		Returns the type of gabarit (lowpass, highpass, stopband, passband or multiband)
		Determine the type if it is not yet determined
		"""
		# determine the type from the list of pass/stop bands
		if self._type is None:
			passBands = [b.isPassBand for b in self._bands]
			if len(self._bands) == 2 and passBands == [True, False]:
				self._type = 'lowpass'
			elif len(self._bands) == 2 and passBands == [False, True]:
				self._type = 'highpass'
			elif len(self._bands) == 3 and passBands == [True, False, True]:
				self._type = 'bandstop'
			elif len(self._bands) == 3 and passBands == [False, True, False]:
				self._type = 'bandpass'
			else:
				self._type = 'multiband'

		return self._type

	@property
	def bands(self):
		return self._bands

	def to_dTF(self, ftype='butter', method='scipy', designMargin=0, centeredZero=False):
		"""
		This methods HELPS to find a transfer function that *should* satisfy the gabarit
		It is just here to quickly determine a transfer function that satisfy the gabarit in a simple way
		But it cannot handle all the options these tools (matlab/scipy) offer (the best is to use these tools the way
		you want, with all the possible options, and then to check if the transfer function fulfills the gabarit

		Parameters:
		-ftype : (str) the type of IIR filter to design:
			- Butterworth   : 'butter'
			- Chebyshev I   : 'cheby1'
			- Chebyshev II  : 'cheby2'
			- Cauer/elliptic: 'ellip'
			- Bessel/Thomson: 'bessel'
		- method: (string) the method used ('scipy' for scipy.signal.iirdesign, 'matlab' for matlab fdesign functions)
		- designMargin: margin (in dB) the designer wants to add to its design (positive reduce the band)

		Returns a transfer function (dTF object)
		"""
		# Start Matlab if needed
		matlabEng = None
		if method == 'matlab' and isMatlabInstalled():
			matlabEng = MatlabHelper(raiseError=False)

		# normalize bands (with pass gain centered in 0dB)
		centerPassGain = max((b.passGains[0]+b.passGains[1])/2.0 for b in self._bands if b.isPassBand)
		bands = [b-centerPassGain for b in self._bands]
		for b in bands:
			b.applyDesignMargin(designMargin)

		# arguments for matlab/scipy functions, for each type of band
		if self.type == 'lowpass':
			passb, stopb = bands
			matlabParams = [passb.w2, stopb.w1, -passb.passGains[0], -stopb.stopGain]
			scipyParams = [passb.w2, stopb.w1, -passb.passGains[0], -stopb.stopGain]

		elif self.type == 'highpass':
			stopb, passb = bands
			matlabParams = [stopb.w2, passb.w1, -stopb.stopGain, -passb.passGains[0]]
			scipyParams = [passb.w1, stopb.w2, -passb.passGains[0], -stopb.stopGain]

		elif self.type == 'bandpass':
			stop1b, passb, stop2b = bands
			matlabParams = [stop1b.w2, passb.w1, passb.w2, stop2b.w1, -stop1b.stopGain, -passb.passGains[0], -stop2b.stopGain]
			scipyParams = [[passb.w1, passb.w2], [stop1b.w2, stop2b.w1], -passb.passGains[0], -stop1b.stopGain]
			if not matlabEng and stop1b.stopGain != stop2b.stopGain:
					raise ValueError("Scipy cannot handle bandpass when the two stop band have different gains")

		elif self.type == 'bandstop':
			pass1b, stopb, pass2b = bands
			matlabParams = [pass1b.w2, stopb.w1, stopb.w2, pass2b.w1, -pass1b.passGains[0], -stopb.stopGain, -pass2b.passGains[0]]
			scipyParams = [[pass1b.w2, pass2b.w1], [stopb.w1, stopb.w2], -pass1b.passGains[0], -stopb.stopGain]
			if not matlabEng and pass1b.passGains[0] != pass1b.passGains[0]:
					raise ValueError("Scipy cannot handle bandstop when the two pass bands have different gains")


		else:
			raise ValueError("Cannot (yet) handle multibands gabarit.")

		# call matlab or scipy methods
		if matlabEng:
			# call fdesign.lowpass/highpass/bandpass/bandstop functions, according to self.type
			try:
				de = matlabEng.fdesign.__getattr__(self.type)(*matlabParams)
				h = matlabEng.design(de, ftype, 'SystemObject', 1)
			except Exception as e:
				raise ValueError("Matlab cannot deal with the following gabarit:\n%s\n%s" % (self, e))
			numM, denM = matlabEng.tf(h, nargout=2)
			# transform to numpy array
			num = array(numM._data.tolist())
			den = array(denM._data.tolist())
		else:
			num, den = iirdesign(*scipyParams, analog=False, ftype=ftype)

		if not centeredZero:
			# go back to pass gain not centered in 0dB
			num = num*10**(centerPassGain/20.0)

		return dTF(num, den)


	def plot(self, tf=None, dB=True):
		"""
		Plot a gabarit , and a transfer function (if given)
		The y-scale can be in dB or not
		Parameters:
			- tf: (dTF) the transfer function to plot
			- dB: (boolean)
		"""
		minG = -200
		if tf:
			w, h = freqz(tf.num.transpose(), tf.den.transpose())
			if dB:
				plt.plot((self._Fs * 0.5 / pi) * w, 20*log10(abs(h)))
				minG = min(20 * log10(abs(h)))
			else:
				plt.plot((self._Fs * 0.5 / pi)*w, abs(h))


		currentAxis = plt.gca()
		for b in self._bands:
			currentAxis.add_patch(b.Rectangle(dB, minG))

		plt.show()




	def check_dTF(self, tf, margin=0, prec=165):
		"""
		Check if a transfer function satisfy the Gabarit
		This is done using Sollya and gabarit.sol

		Parameters:
		- tf: (dTF) transfer function we want to check
		- margin: margin we can tolerate in the check (not in dB)
		- prec: (int) precision in bits given to Sollya.checkModulusFilterInSpecification

		Returns a tuple (isOk, res)
		- isOk: True if the transfer function is in the gabarit
		- res: sollya object embedded the result
		"""

		Gabarit.readyToRunWithSollya()

		# get num,den as sollya objects
		num, den = tf.to_Sollya()

		# build the constraints to verify
		constraints = [b.sollyaConstraint(margin) for b in self._bands]

		# run sollya check
		# print("-> calling checkModulusFilterInSpecification")
		res = sollya.parse("checkModulusFilterInSpecification")(num, den, constraints, prec)
		sollya.parse("presentResults")(res)

		return dict(res)["okay"], res



	def findMinimumMargin(self, tf, initMargin=0):

		Gabarit.readyToRunWithSollya()

		margin = sollya.round(initMargin, 53, sollya.RU)
		deltaMargin = -infty
		gPass = False
		nbIter = 0
		while (not gPass) and (nbIter < 25):
			nbIter += 1
			# check if margin
			gPass, res = self.check_dTF(tf, margin=margin)
			if not gPass:
				oldDeltaMargin = deltaMargin
				# find the maximum margin we should apply, according to the results
				deltaMargin = findMaxIssue(res)

				if deltaMargin == 0:
					deltaMargin += 10**(1e-3 + self.maxGain()/20) - 10**(self.maxGain()/20)

				#print('deltaMargin='+str(deltaMargin))
				#print('margin='+str(margin))
				# check if we have something to improve
				# check if the margin decrease

				# if the old margin is lower than the new margin, and it is not the first iteration
				if oldDeltaMargin <= deltaMargin and oldDeltaMargin != -infty and margin != 0:
					print(("deltaMargin does not decrease:\n old=%s\n new=%s") % (oldDeltaMargin, deltaMargin))
					# deltaMargin *=2
					# raise ValueError("deltaMargin does not decrease")

				# increase the margin
				# margin += deltaMargin
				margin = sollya.round(deltaMargin+margin, 53, sollya.RU)



		return margin


def iter_random_Gabarit(number, form=None):
	"""
	Generate some random gabarits
	Parameters
	- number: number of gabarit generated
	- form: (string) {None, ‘lowpass’, ‘highpass’, ‘bandpass’, ‘bandstop’}. Gives the type of filter. If None, the type is randomized
	"""
	for x in range(number):
		yield random_Gabarit(form=form)



def random_Gabarit(form=None, seed=None):
	"""
	Generate a random Gabarit
	Parameters:
	- form: (string) {None, ‘lowpass’, ‘highpass’, ‘bandpass’, ‘bandstop’}. Gives the type of filter. If None, the type is randomized
	- seed: if not None, indicates the seed to use for the random part (in order to be reproductible, the seed is stored in the name of the gabarit)
	"""
	# change the seed if asked (otherwise, set the seed)
	if not seed:
		set_seed(None)  # (from doc):  If seed is omitted or None, current system time is used
		seed = randint(0, 16777215)  # between 0 and 2^24-1
	set_seed(seed)


	# choose a form if asked
	if form is None:
		# form = choice(("lowpass", "highpass", "bandpass", "bandstop"))
		form = choice(("lowpass",))

	Fs = randint(500, 100000)

	# lowpass
	if form == 'lowpass':
		Fpass = uniform(0.01, 0.9)*Fs/2  # Wpass between 0.01 and 0.9
		Fstop = uniform(Fpass, Fs/2)     # Wstop between Wpass and 1
		gp = uniform(-5, 5)              # upperband for pass in [-5;5]
		gps = uniform(0.1, 5)            # pass width in [0.1;5]
		gs = uniform(-80, 2*(gp-gps))   # stop band in [-80 and 2*lowerband]
		bands = [(0, Fpass), (Fstop, None)]
		Gains = [(gp, gp-gps), gs]
	else:
		raise ValueError('The form is not valid')

	return Gabarit(Fs, bands, Gains, seed=seed)


def findMaxIssue(res):
	"""
	Find the issue with the maximum error
	Parameters:
	- res: (sollya object) result from the checkModulusFilterInSpecification function

	Returns the maximum value (0 if not available)
	"""
	maxError = 0
	for b in dict(res)["results"]:  # for every band
		okay = dict(b)["okay"]
		if not okay:
			for i in dict(b)["issue"]:  # for every issues
				H = dict(i)["H"]
				betaInf = dict(dict(i)["specification"])["betaInf"]
				betaSup = dict(dict(i)["specification"])["betaSup"]
				if sollya.inf(H) > betaSup:
					maxError = sollya.max(maxError, sollya.sup(H) - betaSup)
				else:
					maxError = sollya.max(maxError, betaSup - sollya.inf(H))

	return maxError
