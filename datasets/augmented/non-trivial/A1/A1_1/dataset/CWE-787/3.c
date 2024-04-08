#include <stdio.h>
#include <stdlib.h>

#define MAX_NAME_LEN 64

char* validate_hostname(char *buffer1, int len){
    if (buffer1 == NULL){
        return NULL;
    }
    char* buffer = malloc(len + 1);
    for (int i = 0; i < len; i++){
        if (buffer1[i] == '-' || buffer1[i] == '.'){
            buffer[i] = ' ';
        }
        else {
            buffer[i] = buffer1[i];
        }
    }
    return buffer;
}

char* get_hostname(char *buffer2, int len){
    char* buffer = malloc(MAX_NAME_LEN);

    char* buffer1 = validate_hostname(buffer2, len);
    if (buffer1 == NULL){
        return NULL;
    }
    strcpy(buffer, buffer1);
    free(buffer1);
    buffer1 = NULL;
    
    return buffer;
}