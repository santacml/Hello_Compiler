#include <stdio.h>

void foo( int val)
{
    printf("The integer is %d\n",  val);
}

/*
this is how it should be
but alas, making args as pointers doesn't work with llvmlite for some reason
note: it does, I just need to use PointerType. stupid past me. oh well.

void foo( int *val)
{
    printf("The integer is %d\n",  *val);
}

int main()
{
    printf("Hello World");
    int a = 123;
    foo(&a);
    return 0;
}
*/

void putBool(int val)
{
    printf("%d\n", val);
}

void putInteger(int val)
{
    printf("%d\n", val);
}

void putFloat(float val)
{
    printf("%f\n", val);
}

void putString(char val[256])
{
    printf("%s\n",val);
}

void putChar(char val)
{
    printf("%c\n", val);
}
