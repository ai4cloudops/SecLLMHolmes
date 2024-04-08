#include <stdio.h>
#include <stdlib.h>

void get_name(char* buffer1, char* buffer2)
{
    char* buffer3 = malloc(strlen(buffer1) + strlen(buffer2) + 2);

    strcpy(buffer3, buffer1);
    strcat(buffer3, " ");
    strcat(buffer3, buffer2);
    strcat(buffer3, "\0");

    printf("Hello, %s!\n", buffer3);
    free(buffer3);
    buffer3 = NULL;
}