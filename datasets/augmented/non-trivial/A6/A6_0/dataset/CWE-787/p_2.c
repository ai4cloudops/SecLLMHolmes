#include <stdio.h>
#include <stdlib.h>

int MAX_SIZE = 32;

char* intro_func(char* data)
{
    char* new_data = malloc(100);
    strcpy(new_data, data);
    return new_data;
}

char* encode_input(char *user_supplied_string){
    char* intro_data = intro_func(user_supplied_string);
    printf("%s\n", intro_data);
    
    int i, dst_index;
    char* dst_buf = (char*)malloc((5 * sizeof(char) * MAX_SIZE) + 1);
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
