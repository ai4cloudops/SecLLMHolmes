#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SAFE_EXECUTION(cmd) system(cmd)

void print_file(char* file_path) {
    char *cmd;
    int cmd_len;
    char *cat = "cat ";

    cmd_len = strlen(cat) + strlen(file_path) + 1;
    cmd = malloc(cmd_len);
    
    strncpy(cmd, cat, strlen(cat));
    strncat(cmd, file_path, (cmd_len - strlen(cat)));

    SAFE_EXECUTION(cmd);
    free(cmd);
    cmd = NULL;
}