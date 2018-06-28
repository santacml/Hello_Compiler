#ifndef foo_h__
#define foo_h__
//gcc -c -Wall -Werror -fpic foo.c
//gcc -shared -o libfoo.so foo.o

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

#endif  // foo_h__
