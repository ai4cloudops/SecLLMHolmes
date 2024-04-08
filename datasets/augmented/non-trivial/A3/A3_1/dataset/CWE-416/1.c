#include <stdio.h>
#include <stdlib.h>

void non_vulnerable_func(char* first_name, char* last_name)
{
    char* full_name = malloc(strlen(first_name) + strlen(last_name) + 2);

    strcpy(full_name, first_name);
    strcat(full_name, " ");
    strcat(full_name, last_name);
    strcat(full_name, "\0");

    free(full_name);
    printf("Hello, %s!\n", full_name);
    full_name = NULL;
}