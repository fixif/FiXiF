#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

double SoP_float(double v0,double v1,double v2,double v3,double v4,double v5,double v6,double v7,double v8)
{
    /*      TP_Float_sop        */
    double r;
    r = 6.98260498046875 * v5 + 4.472015380859375 * v6 + 9.55084228515625 * v0 + 11.200286865234375 * v3 + -0.9401397705078125 * v8 + 2.360076904296875 * v4 + 10.651458740234375 * v7 + 2.76476287841796875 * v2 + 10.5360565185546875 * v1;
	return r; 
}

int16_t C_int(int16_t v0,int16_t v1,int16_t v2,int16_t v3,int16_t v4,int16_t v5,int16_t v6,int16_t v7,int16_t v8)
{
    // Registers declaration
	int32_t r0, r1, r2;
	// Computation of c5*v5 in r0
	r0 = 457612*v5>> 19;
	// Computation of c6*v6 in r1
	r1 = 146539*v6>> 17;
	// Computation of r0+r1 in r0
	r0 = r0 + r1;
	// Computation of c0*v0 in r1
	r1 = 625924*v0>> 17;
	// Computation of r0+r1 in r0
	r0 = r0 + r1;
	// Computation of c3*v3 in r1
	r1 = 367011*v3>> 17;
	// Computation of c8*v8 in r2
	r2 = -61613*v8>> 15;
	// Computation of r1+r2 in r1
	r1 = r1 + r2;
	// Computation of r0+r1 in r0
	r0 = r0 + r1;
	// Computation of c4*v4 in r1
	r1 = 154670*v4>> 17;
	// Computation of c7*v7 in r2
	r2 = 349027*v7>> 17;
	// Computation of r1+r2 in r1
	r1 = r1 + r2;
	// Computation of c2*v2 in r2
	r2 = 362383*v2>> 18;
	// Computation of r1+r2 in r1
	r1 = r1 + r2;
	// Computation of c1*v1 in r2
	r2 = 690491*v1>> 18;
	// Computation of r1+r2 in r1
	r2 = r2 % 1048576;
	r1 = r1 + r2;
	// Computation of r0+r1 in r0
	r0 = r0 + r1;
	// The result is returned with a final right shift
	return r0 >> 4;
}

ac_fixed<15,12,true> SoP_ac_fixed(ac_fixed<19,9,true,AC_TRN> v5,ac_fixed<17,8,true,AC_TRN> v6,ac_fixed<17,9,true,AC_TRN> v0,ac_fixed<17,8,true,AC_TRN> v3,ac_fixed<15,9,true,AC_TRN> v8,ac_fixed<17,9,true,AC_TRN> v4,ac_fixed<17,8,true,AC_TRN> v7,ac_fixed<18,10,true,AC_TRN> v2,ac_fixed<18,9,true,AC_TRN> v1)
{
	//Declaration of sums sd and s
	ac_fixed<19,12,true> sd = 0;
	ac_fixed<15,12,true> s = 0;

	//Computation of c5*v5 in sd
	ac_fixed<20,4,true,AC_TRN> c5 = 6.98260498046875;
	sd = sd + c5*v5;
	//Computation of c6*v6 in sd
	ac_fixed<19,4,true,AC_TRN> c6 = 4.472015380859375;
	sd = sd + c6*v6;
	//Computation of c0*v0 in sd
	ac_fixed<21,5,true,AC_TRN> c0 = 9.55084228515625;
	sd = sd + c0*v0;
	//Computation of c3*v3 in sd
	ac_fixed<20,5,true,AC_TRN> c3 = 11.200286865234375;
	sd = sd + c3*v3;
	//Computation of c8*v8 in sd
	ac_fixed<17,1,true,AC_TRN> c8 = -0.9401397705078125;
	sd = sd + c8*v8;
	//Computation of c4*v4 in sd
	ac_fixed<19,3,true,AC_TRN> c4 = 2.360076904296875;
	sd = sd + c4*v4;
	//Computation of c7*v7 in sd
	ac_fixed<20,5,true,AC_TRN> c7 = 10.651458740234375;
	sd = sd + c7*v7;
	//Computation of c2*v2 in sd
	ac_fixed<20,3,true,AC_TRN> c2 = 2.76476287841796875;
	sd = sd + c2*v2;
	//Computation of c1*v1 in sd
	ac_fixed<21,5,true,AC_TRN> c1 = 10.5360565185546875;
	sd = sd + c1*v1;

	//Computation of the final right shift
	s = s + sd;
	return s;
}
