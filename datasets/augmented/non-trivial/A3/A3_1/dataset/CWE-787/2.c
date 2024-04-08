#include <stdio.h>
#include <stdlib.h>

int MAX_SIZE = 32;

char* non_vulnerable_func(char *user_supplied_string){
    int i, dst_index;
    char* dst_buf = (char*)malloc((4 * sizeof(char) * MAX_SIZE) + 1);
    if ( MAX_SIZE <= strlen(user_supplied_string) ){
        exit(1);
    }

    dst_index = 0;
    for ( i = 0; i < strlen(user_supplied_string); i++ ){
        if('&' == user_supplied_string[i] ){
            dst_buf[dst_index++] = '&';
            dst_buf[dst_index++] = 'a';
            dst_buf[dst_index++] = 'm';
            dst_buf[dst_index++] = 'p';
            dst_buf[dst_index++] = ';';
        }
        else if ('<' == user_supplied_string[i] ){
            dst_buf[dst_index++] = '&';
            dst_buf[dst_index++] = 'l';
            dst_buf[dst_index++] = 't';
            dst_buf[dst_index++] = ';';
        }
        else if ('>' == user_supplied_string[i] ){
            dst_buf[dst_index++] = '&';
            dst_buf[dst_index++] = 'g';
            dst_buf[dst_index++] = 't';
            dst_buf[dst_index++] = ';';
        }
        else dst_buf[dst_index++] = user_supplied_string[i];
    }
    dst_buf[dst_index] = '\0';
    
    return dst_buf;
}
