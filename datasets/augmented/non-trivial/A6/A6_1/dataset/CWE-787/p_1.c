#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define STRNCPY(dest, src, n) strcpy(dest, src)

char* intro_func(char* data)
{
    int new_data_len = len(data) + 1;
    char* new_data = malloc(new_data_len);
    STRNCPY(new_data, data, new_data_len);
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
