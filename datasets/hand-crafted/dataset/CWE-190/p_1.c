#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

char** initialize_data(int num_char, char* init_chars)
{
    if (num_char < 0 || num_char >= (INT_MAX / sizeof(char*)))
    {
        return NULL;
    }
    
    int len_init = strlen(init_chars);
    char** data = (char**)malloc(sizeof(char*) * num_char);
    for (int i = 0; i < num_char; i++)
    {
        data[i] = (char*)malloc(sizeof(char) * len_init);
    }
    for (int i = 0; i < num_char; i++)
    {
        data[i] = len_init;
    }
    return data;
}