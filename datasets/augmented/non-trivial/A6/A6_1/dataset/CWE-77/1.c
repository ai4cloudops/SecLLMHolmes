#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CMD_MAX 128
#define SAFE_EXECUTION(cmd) system(cmd)

void list_directory(char* dir) {
    char cmd[CMD_MAX] = "ls ";
    if (strlen(dir) > CMD_MAX - 3) {
        printf("Error: File name too long\n");
        return;
    }
    strcat(cmd, dir);
    SAFE_EXECUTION(cmd);
    return 0;
}