#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

double SoP_float(double v0,double v1,double v2,double v3,double v4,double v5,double v6,double v7,double v8)
{
    /*      TP_Float_sop        */
    double r;
    r = 0.253330707550048828125 * v0 + 0.0609569549560546875 * v1 + 0.176759243011474609375 * v2 + -0.3001334667205810546875 * v3 + 0.1632754802703857421875 * v4 + 0.382720947265625 * v5 + 0.4687969684600830078125 * v6 + -0.112518310546875 * v7 + 0.264287471771240234375 * v8;
	return r; 
}

int16_t C_int(int16_t v0,int16_t v1,int16_t v2,int16_t v3,int16_t v4,int16_t v5,int16_t v6,int16_t v7,int16_t v8)
{
    // Registers declaration
	int32_t r0, r1;
	// Computation of c0*v0 in r0
	r0 = 1062546*v0>> 17;
	// Computation of c1*v1 in r1
	r1 = 255672*v1>> 17;
	// Computation of r0+r1 in r0
	r0 = r0 + r1;
	// Computation of c2*v2 in r1
	r1 = 370691*v2>> 14;
	// Computation of r0+r1 in r0
	r0 = r0 + r1;
	// Computation of c3*v3 in r1
	r1 = -2517702*v3>> 18;
	// Computation of r0+r1 in r0
	r0 = r0 + r1;
	// Computation of c4*v4 in r1
	r1 = 684827*v4>> 17;
	// Computation of r0+r1 in r0
	r0 = r0 + r1;
	// Computation of c5*v5 in r1
	r1 = 3210496*v5>> 18;
	// Computation of r0+r1 in r0
	r0 = r0 + r1;
	// Computation of c6*v6 in r1
	r1 = 3932554*v6>> 19;
	// Computation of r0+r1 in r0
	r0 = r0 + r1;
	// Computation of c7*v7 in r1
	r1 = -235968*v7>> 15;
	// Computation of r0+r1 in r0
	r0 = r0 + r1;
	// Computation of c8*v8 in r1
	r1 = 554251*v8>> 17;
	// Computation of r0+r1 in r0
	r0 = r0 >> 1;
	r1 = r1 >> 1;
	r0 = r0 + r1;
	// The result is returned with a final right shift
	return r0 >> 4;
}

ac_fixed<19,11,true> SoP_ac_fixed(ac_fixed<17,10,true,AC_TRN> v0,ac_fixed<17,10,true,AC_TRN> v1,ac_fixed<14,9,true,AC_TRN> v2,ac_fixed<18,11,true,AC_TRN> v3,ac_fixed<17,10,true,AC_TRN> v4,ac_fixed<18,11,true,AC_TRN> v5,ac_fixed<19,11,true,AC_TRN> v6,ac_fixed<15,9,true,AC_TRN> v7,ac_fixed<17,9,true,AC_TRN> v8)
{
	//Declaration of sums sd and s
	ac_fixed<23,11,true> sd = 0;
	ac_fixed<19,11,true> s = 0;

	//Computation of c0*v0 in sd
	ac_fixed<22,0,true,AC_TRN> c0 = 0.253330707550048828125;
	sd = sd + c0*v0;
	//Computation of c1*v1 in sd
	ac_fixed<19,-3,true,AC_TRN> c1 = 0.0609569549560546875;
	sd = sd + c1*v1;
	//Computation of c2*v2 in sd
	ac_fixed<20,-1,true,AC_TRN> c2 = 0.176759243011474609375;
	sd = sd + c2*v2;
	//Computation of c3*v3 in sd
	ac_fixed<23,0,true,AC_TRN> c3 = -0.3001334667205810546875;
	sd = sd + c3*v3;
	//Computation of c4*v4 in sd
	ac_fixed<21,-1,true,AC_TRN> c4 = 0.1632754802703857421875;
	sd = sd + c4*v4;
	//Computation of c5*v5 in sd
	ac_fixed<23,0,true,AC_TRN> c5 = 0.382720947265625;
	sd = sd + c5*v5;
	//Computation of c6*v6 in sd
	ac_fixed<23,0,true,AC_TRN> c6 = 0.4687969684600830078125;
	sd = sd + c6*v6;
	//Computation of c7*v7 in sd
	ac_fixed<19,-2,true,AC_TRN> c7 = -0.112518310546875;
	sd = sd + c7*v7;
	//Computation of c8*v8 in sd
	ac_fixed<21,0,true,AC_TRN> c8 = 0.264287471771240234375;
	sd = sd + c8*v8;

	//Computation of the final right shift
	s = s + sd;
	return s;
}
