#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char* intro_func(char* data)
{
    char* new_data = malloc(100);
    strcpy(new_data, data);
    return new_data;
}

int main(int argc, char** argv)
{
    char* intro_data = intro_func(argv[1]);
    printf("%s\n", intro_data);

    int buf[3];

    buf[0] = 167;
    buf[1] = 249;
    buf[2] = 367;

    return 0;
}
