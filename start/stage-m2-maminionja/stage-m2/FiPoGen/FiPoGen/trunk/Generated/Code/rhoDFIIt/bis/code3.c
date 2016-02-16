#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

double SoP_float(double v0)
{
    /*      TP_Float_sop        */
    double r;
    r = 0.88358306884765625 * v0;
	return r; 
}

int16_t C_int(int16_t v0)
{
    // Registers declaration
	// Computation of c0*v0 in r0
	r0 = 231626*v0>> 18;
	// The result is returned 	return r0;
}

ac_fixed<18,12,true> SoP_ac_fixed(ac_fixed<18,12,true,AC_TRN> v0)
{
	//Declaration of sums sd and s
	ac_fixed<18,12,true> sd = 0;
	ac_fixed<18,12,true> s = 0;

	//Computation of c0*v0 in sd
	ac_fixed<19,1,true,AC_TRN> c0 = 0.88358306884765625;
	sd = sd + c0*v0;

	//Computation of the final right shift
	s = s + sd;
	return s;
}
