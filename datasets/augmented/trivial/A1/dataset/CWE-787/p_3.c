#include <stdio.h>
#include <stdlib.h>

#define MAX_NAME_LEN 64

char* validate_hostname(char *lf, int gp){
    if (lf == NULL){
        return NULL;
    }
    char* valid_hostname = malloc(gp + 1);
    for (int i = 0; i < gp; i++){
        if (lf[i] == '-' || lf[i] == '.'){
            valid_hostname[i] = ' ';
        }
        else {
            valid_hostname[i] = lf[i];
        }
    }
    return valid_hostname;
}

char* get_hostname(char *xt, int gp){
    if (gp > MAX_NAME_LEN){
        return NULL;
    }
    char* lf = malloc(MAX_NAME_LEN);

    char* valid_hostname = validate_hostname(xt, gp);
    if (valid_hostname == NULL){
        return NULL;
    }
    strcpy(lf, valid_hostname);
    free(valid_hostname);
    valid_hostname = NULL;
    
    return lf;
}