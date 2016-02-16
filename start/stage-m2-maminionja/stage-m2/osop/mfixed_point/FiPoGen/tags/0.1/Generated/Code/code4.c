#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

double SoP_float(int16_t x0,int16_t x1,int16_t x2)
{
    /*      TP_Float_sop        */
    double r;
    ((-0.14199066162109375 * x1*pow(2,-11) + 0.0002717077732086181640625 * x2*pow(2,-9)) + 0.880828857421875 * x0*pow(2,-11))
	return r*powf(2.f,-11); ;
}

int16_t SoP_int(int16_t x0,int16_t x1,int16_t x2)
{
    /*      TP_Int_dec        */
    

    
    /*      TP_Int_sop        */
	int16 c, x;
	int32 r0, r1, r2, r3;

	//Computation of c1*x1 in register r0
	c = -18611;
	r0 = c*x1;

	//Computation of c2*x2 in register r1
	c = 18234;
	r1 = c*x2;

	//Computation of r0+r1 in register r2
	r2= r0 + ( r1 >> 7 );

	//Computation of c0*x0 in register r0
	c = 28863;
	r0 = c*x0;

	//Computation of r2+r0 in register r1
	r1= ( r2 >> 1 ) + ( r0 << 1 );

	//Computation of the final right shift
	r2= r1 >> 16 ;
	return r2;
}

/* double SoP_ac_fixed(float tab[int16_t x0,int16_t x1,int16_t x2])
{
          TP_Float        
    
	float L1 = tab[1]*pow(2,-11);
	float L2 = tab[2]*pow(2,-9);
	float L0 = tab[0]*pow(2,-11);

    
          TP_Float        

	//Computation of c1*x1 in register r0
	ac_fixed<16,-1,true,AC_TRN> c1 = -0.14199066162109375;
	ac_fixed<16,5,true,AC_TRN> x1 = L1;
	ac_fixed<32,4,true,AC_TRN> r0 = c1*x1;


	//Computation of c2*x2 in register r1
	ac_fixed<16,-10,true,AC_TRN> c2 = 0.0002717077732086181640625;
	ac_fixed<16,7,true,AC_TRN> x2 = L2;
	ac_fixed<32,-3,true,AC_TRN> r1 = c2*x2;


	//Computation of r0+r1 in register r2
	ac_fixed<32,4,true,AC_TRN> r2 = r0 + r1;

	//Computation of c0*x0 in register r3
	ac_fixed<16,1,true,AC_TRN> c0 = 0.880828857421875;
	ac_fixed<16,5,true,AC_TRN> x0 = L0;
	ac_fixed<32,6,true,AC_TRN> r3 = c0*x0;


	//Computation of r2+r3 in register r4
	ac_fixed<32,5,true,AC_TRN> r4 = r2 + r3;

	//Computation of the final right shift
	ac_fixed<16,5,true,AC_TRN> r5 = r4;
	double res = r5.to_double();
	return res;
}*/
