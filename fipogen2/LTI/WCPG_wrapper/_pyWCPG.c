#include <Python.h>
#include <numpy/arrayobject.h>

//extern int WCPG_ABCD(double W, double A, double B, double C, double D, uint64_t n, uint64_t p, uint64_t q);
#include "libwcpg.h"

#include <dlfcn.h>

#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION

// Best tuto
// http://dan.iel.fm/posts/python-c-extensions/

static char module_docstring[] =

   "This module imports calculation of WCPG with double precision and hopefully in the future other things." ;
   
static char pyWCPG_docstring[] =

   "For an LTI filter given in its State-Space representation {A,B,C,D}, \
where A is n*n, B is n*q, C is p*n and D is p*q real matrix the function \
returns integer value indicating if WCPG was successfully computed. \
In p*q matrix W the Worst-Case peak gain is stored if algorithm successfully exited. \
Input: \
	A, B, C, D - pointers for double arrays representing filter in state-space realization \
	n, p, q - order of filter, number of inputs and number of outputs respectively \
	W (output) - if function succeeds, on the output will hold the p*q size WCPG matrix of the filter {A,B,C,D} \
				space for W is assumed to be preallocated outside the function \
Output: \
	integer value equal to 1 if WCPG computation is successful and 0 otherwise." ;

static PyObject *WCPG_pyWCPG(PyObject *self, PyObject *args) ;
	
static PyMethodDef module_methods[] = {
   {"pyWCPG", WCPG_pyWCPG, METH_VARARGS, pyWCPG_docstring},
   {NULL, NULL, 0, NULL}
} ;

PyMODINIT_FUNC init_pyWCPG(void)
{
  PyObject *m = Py_InitModule3("_pyWCPG", module_methods, module_docstring);
  
  if (m == NULL){
    return;
  };
  
  /* Load other needed stuff from python here*/
  /*Ex : load 'numpy' functionality*/
  import_array() ;
  
} ;

// This is the function that we're going to call in the python code

static PyObject *WCPG_pyWCPG(PyObject *self, PyObject *args)
{
//int WCPG_ABCD(double *W, double *A, double *B, double *C, double *D, uint64_t n, uint64_t p, uint64_t q);
  
  PyObject *W_obj, *A_obj, *B_obj, *C_obj, *D_obj ;
  
  int n, p, q = 0;
  
  /* Parse incoming tuple */
  
  if (!PyArg_ParseTuple(args, "OOOOOiii", &W_obj, &A_obj, &B_obj, &C_obj, &D_obj, &n, &p, &q))
  {
    return NULL;
  }

  /* Interpret objects part of the tuple */
  /* W, A, B, C, D*/
  
  PyObject *W_loc = PyArray_FROM_OTF(W_obj, NPY_DOUBLE, NPY_IN_ARRAY) ; // NP_INOUT_ARRAY
  
  PyObject *A_loc = PyArray_FROM_OTF(A_obj, NPY_DOUBLE, NPY_IN_ARRAY) ;
  PyObject *B_loc = PyArray_FROM_OTF(B_obj, NPY_DOUBLE, NPY_IN_ARRAY) ;
  PyObject *C_loc = PyArray_FROM_OTF(C_obj, NPY_DOUBLE, NPY_IN_ARRAY) ;
  PyObject *D_loc = PyArray_FROM_OTF(D_obj, NPY_DOUBLE, NPY_IN_ARRAY) ;
  
if (W_loc == NULL || A_loc == NULL || B_loc == NULL || C_loc == NULL || D_loc == NULL) {
  
  Py_XDECREF(W_loc) ;
  
  Py_XDECREF(A_loc) ;
  Py_XDECREF(B_loc) ;
  Py_XDECREF(C_loc) ;
  Py_XDECREF(D_loc) ;
  
  return NULL ;
  
} ;

 // Create new array W with good size

  double W[q*p] ;
  
/* Get pointers to the data as C-types */

  //double *W = (double*)PyArray_DATA(W_loc) ;
  
  double *A = (double*)PyArray_DATA(A_loc) ;
  double *B = (double*)PyArray_DATA(B_loc) ;
  double *C = (double*)PyArray_DATA(C_loc) ;
  double *D = (double*)PyArray_DATA(D_loc) ;

  /*Open .so and use*/
  
  void *handle ;
  char *error ;
  int  (*WCPG_ABCD)(double*, double*, double*, double*, double*, uint64_t, uint64_t, uint64_t) ;
  
  //handle = dlopen("./libWCPG.so.0.0.9", RTLD_LAZY) ;
  handle = dlopen("libwcpg.so", RTLD_GLOBAL | RTLD_LAZY) ;
  
  if (!handle) {
   fprintf(stderr, "%s\n", dlerror()) ;
   exit(EXIT_FAILURE) ;
  } ;
  
  dlerror(); // clear any existing error, see http://linux.die.net/man/3/dlopen
  
  *(void **) (&WCPG_ABCD) = dlsym(handle, "WCPG_ABCD") ;
  
  if ((error = dlerror()) != NULL) {
   fprintf(stderr, "%s\n", dlerror()) ;
   exit(EXIT_FAILURE) ; 
  } ;
  
  int loc_n, loc_p, loc_q ;
  
  
  
  loc_n = (uint64_t)n ;
  loc_p = (uint64_t)p ;
  loc_q = (uint64_t)q ;
  
  //WCPG_ABCD(double *W, double *A, double *B, double *C, double *D, uint64_t n, uint64_t p, uint64_t q);
  
  (*WCPG_ABCD)(W, A, B, C, D, loc_n, loc_p, loc_q) ;
  
  dlclose(handle) ;
  
    int i, j, k ;
  
//   fprintf(stdout,"A= \n");
//   fprintf(stdout, "%f ",A[i]);
  
  i = 0 ;
  j = 0 ;
  k = 0 ;
  
  
  // Reshape the array, 2d array, not a list.
  
  double tmp_tab[q][p] ;
  
  for (i=0 ; i<q ; i++)
  {
    k = q*i ;
    for (j=0 ; j<p ; j++)
    {
      tmp_tab[i][j] = W[k+j];
    }
  }
  
  /* Build the output tuple */
  
  /* W is an n*n matrix */
  /* http://docs.scipy.org/doc/numpy/reference/c-api.dtype.html */
  
  /* Dimension of array W n*n*/
  npy_intp dims[2] ;
  dims[0] = q ;
  dims[1] = p ;

  PyObject *Wobj = PyArray_SimpleNewFromData(2, dims, NPY_DOUBLE, W) ;
  
  Py_INCREF(Wobj) ;
  
  /* DEBUG */
  
  fprintf(stdout, "====================================== \n");
  fprintf(stdout, "n = %i \n", n);
  fprintf(stdout, "q = %i \n",(int)dims[0]) ;
  fprintf(stdout, "p = %i \n",(int)dims[1]) ;
  fprintf(stdout, "====================================== \n");
  

  
  /*==============================================*/
  
  fprintf(stdout,"A = \n");
  
  for (i=0; i<n ; i++)
  {
    
    k = n*i ;
    
    for (j=0; j<n ; j++)
    {
      fprintf(stdout, "%f ",A[k+j]);
    }
    
    fprintf(stdout, "\n");
    
  }

    /*==============================================*/
  
  fprintf(stdout,"B = \n");
  
  for (i=0; i<n ; i++)
  {
    
    k = n*i ;
    
    for (j=0; j<p ; j++)
    {
      fprintf(stdout, "%f ",B[k+j]);
    }
    
    fprintf(stdout, "\n");
    
  }
  
    /*==============================================*/
  
  fprintf(stdout,"C = \n");
  
  for (i=0; i<q ; i++)
  {
    
    k = q*i ;
    
    for (j=0; j<n ; j++)
    {
      fprintf(stdout, "%f ",C[k+j]);
    }
    
    fprintf(stdout, "\n");
    
  }
  
    /*==============================================*/
  
  fprintf(stdout,"D = \n");
  
  for (i=0; i<q ; i++)
  {
    
    k = q*i ;
    
    for (j=0; j<p ; j++)
    {
      fprintf(stdout, "%f ",D[k+j]);
    }
    
    fprintf(stdout, "\n");
    
  }
  
    /*==============================================*/
    
  fprintf(stdout,"W = \n");
  
  for (i=0; i<q ; i++)
  {
    
    k = q*i ;
    
    for (j=0; j<p ; j++)
    {
      fprintf(stdout, "%f ",W[k+j]);
    }

    fprintf(stdout, "\n");
    
  }    
  
//   for (i=0; i<n*n; i++){
//     
//       j += 1 ;
//   
//       if (j%q >= 1)
//       {
// 	fprintf(stdout, "\n");
// 	j=0;
//       }
//       
//       fprintf(stdout, "%f ",A[i]);
//   }
  
//   fprintf(stdout, "\n");
//   
//     fprintf(stdout,"W= \n");
//   for (i=0; i<p*q; i++)
//       fprintf(stdout, "%f ",W[i]);
//   fprintf(stdout, "\n");
  

  
 // Py_DECREF(n) ;
 // Py_DECREF(p) ;
 // Py_DECREF(q) ;
  
    /*clean all vars not result, python-side*/
  
  Py_DECREF(A_loc) ;
  Py_DECREF(B_loc) ;
  Py_DECREF(C_loc) ;
  Py_DECREF(D_loc) ;
  Py_DECREF(W_loc) ;
  
  
  // Not needed because those are not python objects (?)

  //Py_DECREF(p) ;
  //Py_DECREF(q) ;
  
  
  return Wobj;
  
}