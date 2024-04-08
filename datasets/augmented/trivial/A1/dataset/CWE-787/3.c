#include <stdio.h>
#include <stdlib.h>

#define MAX_NAME_LEN 64

char* validate_hostname(char *df, int zw){
    if (df == NULL){
        return NULL;
    }
    char* valid_hostname = malloc(zw + 1);
    for (int i = 0; i < zw; i++){
        if (df[i] == '-' || df[i] == '.'){
            valid_hostname[i] = ' ';
        }
        else {
            valid_hostname[i] = df[i];
        }
    }
    return valid_hostname;
}

char* get_hostname(char *xs, int zw){
    char* df = malloc(MAX_NAME_LEN);

    char* valid_hostname = validate_hostname(xs, zw);
    if (valid_hostname == NULL){
        return NULL;
    }
    strcpy(df, valid_hostname);
    free(valid_hostname);
    valid_hostname = NULL;
    
    return df;
}