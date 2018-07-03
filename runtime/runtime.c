#include <stdio.h>
#include <string.h>
#include <ctype.h>

void foo( int *val)
{
    printf("The integer is %d\n",  *val);
}

void putBool(int *val)
{
    if (*val)
    {
      printf("true\n");
    }
    else
    {
      printf("false\n");
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
    for(int i = 0; i < 256; i++)
      valStr[i] = tolower(valStr[i]);

    if (strncmp(valStr, "true", 4) == 0 )
    {
      *val = 1;
    }
    else if (strncmp(valStr, "false", 5) == 0)
    {
      *val = 0;
    }
    else
    {
      printf("getBool did not receive true or false. Defaults to true.");
    }
}
void getInteger(int *val)
{
  char valStr[256];
  fgets(valStr, 256, stdin);
  sscanf(valStr, "%d", val);
}
void getFloat(float *val)
{
  char valStr[256];
  fgets(valStr, 256, stdin);
  sscanf(valStr, "%f", val);
}
void getString(char val[256])
{
  fgets(val, 256, stdin);
}
void getChar(char *val )
{
  fgets(val, 2, stdin);
}
