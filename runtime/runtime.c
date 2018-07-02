#include <stdio.h>

void foo( int *val)
{
    printf("The integer is %d\n",  *val);
}

void putBool(int *val)
{
    if (*val)
    {
      printf("true");
    }
    else
    {
      printf("false");
    }
}

void putInteger(int *val)
{
    printf("%d\n", *val);
}

void putFloat(float *val)
{
    printf("%f\n", *val);
}

void putString(char val[256])
{
    printf("%s\n",val);
}

void putChar(char val)
{
    printf("%c\n", val);
}

void getBool( int *val)
{
  char valStr[256];
  fgets(valStr, 256, stdin);
  *val = 
}
void getInteger(int *val)
{

}
void getFloat(float *val)
{

}
void getString(char *val[])
{

}
void getChar(char *val )
{

}
