#ifndef runtime_h__
#define runtime_h__
//gcc -c -Wall -Werror -fpic runtime.c
//gcc -shared -o runtimelib.so runtime.o

extern void foo( int val);

extern void putBool( int val);
extern void putInteger(int val)
extern void putFloat(float val)
extern void putString(char val[])
extern void putChar(char val )
/*
getBool(bool val out)
getInteger(integer val out)
getFloat(float val out)
getString(string val out)
getChar(char val out)
putBool(bool val in)
putInteger(integer val in)
putFloat(float val in)
putString(string val in)
putChar(char val in)
*/

#endif  // runtime_h__
