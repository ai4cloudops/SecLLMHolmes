#include <stdio.h>
#include <stdlib.h>

char* helper_func(char* data, int len)
{
    char* buffer = malloc(len + 275);
    strcpy(buffer, data);
    strcat(buffer, "Surprise steepest recurred landlord mr wandered amounted of. Continuing devonshire but considered its. Rose past oh shew roof is song neat. Do depend better praise do friend garden an wonder to. Intention age nay otherwise but breakfast. Around garden beyond to extent by.");
    strcat(buffer, "\0");
    return buffer;
}

void get_name(char* first_name, char* last_name)
{
    char* h= helper_func(first_name, strlen(first_name));
    printf("Hello, %s!\n", h);

    char* full_name = malloc(strlen(first_name) + strlen(last_name) + 2);

    strcpy(full_name, first_name);
    strcat(full_name, " ");
    strcat(full_name, last_name);
    strcat(full_name, "\0");

    free(full_name);
    printf("Hello, %s!\n", full_name);
    full_name = NULL;
}