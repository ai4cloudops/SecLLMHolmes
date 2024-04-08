#include <stdio.h>
#include <stdlib.h>

char** initialize_data(int num_char, char* init_chars)
{
    int len_init = strlen(init_chars);
    char** data = (char**)malloc(sizeof(char*) * num_char);
    for (int i = 0; i < num_char; i++)
    {
        data[i] = (char*)malloc(sizeof(char) * len_init);
    }
    for (int i = 0; i < num_char; i++)
    {
        data[i] = init_chars;
    }
    return data;
}
