#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

double SoP_float(double v0,double v1,double v2,double v3)
{
    /*      TP_Float_sop        */
    double r;
    r = 0.795928955078125 * v1 + 0.023296356201171875 * v2 + 0.12245845794677734375 * v0 + 1 * v3;
	return r; 
}

int16_t C_int(int16_t v0,int16_t v1,int16_t v2,int16_t v3)
{
    // Registers declaration
	int32_t r0, r1, r2;
	// Computation of c1*v1 in r0
	r0 = 52162*v1>> 18;
	// Computation of c2*v2 in r1
	r1 = 6107*v2>> 16;
	// Computation of r0+r1 in r0
	r0 = r0 + r1;
	// Computation of c0*v0 in r1
	r1 = 256814*v0>> 20;
	// Computation of c3*v3 in r2
	r2 = 16384*v3>> 13;
	// Computation of r1+r2 in r1
	r1 = r1 + r2;
	// Computation of r0+r1 in r0
	r0 = r0 + r1;
	// The result is returned with a final right shift
	return r0 >> 2;
}

/* double SoP_ac_fixed(float tab[int16_t v0,int16_t v1,int16_t v2,int16_t v3])
{
          TP_Float        
    
	float L1 = tab[1]*pow(2,-9);
	float L2 = tab[2]*pow(2,-5);
	float L0 = tab[0]*pow(2,-6);
	float L3 = tab[3]*pow(2,-6);

    
          TP_Float        

	//Computation of c1*v1 in register r0
	ac_fixed<17,1,true,AC_TRN> c1 = 0.795928955078125;
	ac_fixed<18,9,true,AC_TRN> v1 = L1;
	ac_fixed<16,9,true,AC_TRN> r0 = c1*v1;


	//Computation of c2*v2 in register r1
	ac_fixed<14,-4,true,AC_TRN> c2 = 0.023296356201171875;
	ac_fixed<16,11,true,AC_TRN> v2 = L2;
	ac_fixed<13,6,true,AC_TRN> r1 = c2*v2;


	//Computation of r0+r1 in register r2
	ac_fixed<16,9,true,AC_TRN> r2 = r0 + r1;

	//Computation of c0*v0 in register r3
	ac_fixed<19,-2,true,AC_TRN> c0 = 0.12245845794677734375;
	ac_fixed<20,14,true,AC_TRN> v0 = L0;
	ac_fixed<18,11,true,AC_TRN> r3 = c0*v0;


	//Computation of c3*v3 in register r4
	ac_fixed<16,2,true,AC_TRN> c3 = 1;
	ac_fixed<13,7,true,AC_TRN> v3 = L3;
	ac_fixed<14,7,true,AC_TRN> r4 = c3*v3;


	//Computation of r3+r4 in register r5
	ac_fixed<18,11,true,AC_TRN> r5 = r3 + r4;

	//Computation of r2+r5 in register r6
	ac_fixed<18,11,true,AC_TRN> r6 = r2 + r5;

	//Computation of the final right shift
	ac_fixed<16,11,true,AC_TRN> r7 = r6;
	double res = r7.to_double();
	return res;
}*/
