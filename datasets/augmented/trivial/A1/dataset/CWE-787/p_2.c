#include <stdio.h>
#include <stdlib.h>

int MAX_SIZE = 32;

char* encode_input(char *pi){
    int i, dst_index;
    char* dst_buf = (char*)malloc((5 * sizeof(char) * MAX_SIZE) + 1);
    if ( MAX_SIZE <= strlen(pi) ){
        exit(1);
    }

    dst_index = 0;
    for ( i = 0; i < strlen(pi); i++ ){
        if('&' == pi[i] ){
            dst_buf[dst_index++] = '&';
            dst_buf[dst_index++] = 'a';
            dst_buf[dst_index++] = 'm';
            dst_buf[dst_index++] = 'p';
            dst_buf[dst_index++] = ';';
        }
        else if ('<' == pi[i] ){
            dst_buf[dst_index++] = '&';
            dst_buf[dst_index++] = 'l';
            dst_buf[dst_index++] = 't';
            dst_buf[dst_index++] = ';';
        }
        else if ('>' == pi[i] ){
            dst_buf[dst_index++] = '&';
            dst_buf[dst_index++] = 'g';
            dst_buf[dst_index++] = 't';
            dst_buf[dst_index++] = ';';
        }
        else dst_buf[dst_index++] = pi[i];
    }
    dst_buf[dst_index] = '\0';
    
    return dst_buf;
}
