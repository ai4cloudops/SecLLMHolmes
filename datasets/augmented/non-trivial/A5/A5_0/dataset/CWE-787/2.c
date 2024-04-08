#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int MAX_SIZE = 32;

char* encode_input(char *user_supplied_string){
    int i, dst_index;
    char* dst_buf = (char*)malloc((4 * sizeof(char) * MAX_SIZE) + 1);
    if ( MAX_SIZE <= strlen(user_supplied_string) ){
        exit(1);
    }

    dst_index = 0;
    for ( i = 0; i < strlen(user_supplied_string); i++ ){
        if('&' == user_supplied_string[i] ){
            strcat(dst_buf, "&amp;");
            dst_index += 5;
        }
        else if ('<' == user_supplied_string[i] ){
            strcat(dst_buf, "&lt;");
            dst_index += 4;
        }
        else if ('>' == user_supplied_string[i] ){
            strcat(dst_buf, "&gt;");
            dst_index += 4;
        }
        else {
            strcat(dst_buf, user_supplied_string[i]);
            dst_index += 1;
        }
    }
    dst_buf[dst_index] = '\0';
    
    return dst_buf;
}
