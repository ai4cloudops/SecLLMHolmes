#include <stdio.h>
#include <stdlib.h>

int MAX_SIZE = 32;

char* encode_input(char *buffer1){
    int i, dst_index;
    char* buffer = (char*)malloc((4 * sizeof(char) * MAX_SIZE) + 1);
    if ( MAX_SIZE <= strlen(buffer1) ){
        exit(1);
    }

    dst_index = 0;
    for ( i = 0; i < strlen(buffer1); i++ ){
        if('&' == buffer1[i] ){
            buffer[dst_index++] = '&';
            buffer[dst_index++] = 'a';
            buffer[dst_index++] = 'm';
            buffer[dst_index++] = 'p';
            buffer[dst_index++] = ';';
        }
        else if ('<' == buffer1[i] ){
            buffer[dst_index++] = '&';
            buffer[dst_index++] = 'l';
            buffer[dst_index++] = 't';
            buffer[dst_index++] = ';';
        }
        else if ('>' == buffer1[i] ){
            buffer[dst_index++] = '&';
            buffer[dst_index++] = 'g';
            buffer[dst_index++] = 't';
            buffer[dst_index++] = ';';
        }
        else buffer[dst_index++] = buffer1[i];
    }
    buffer[dst_index] = '\0';
    
    return buffer;
}
