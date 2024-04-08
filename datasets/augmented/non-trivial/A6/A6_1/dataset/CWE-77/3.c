#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SAFE_EXECUTION(cmd) system(cmd)

char* validate_cmd(char* cmd) {
    char* new_cmd = malloc(strlen(cmd) + 1);
    int cmd_ix = 0;
    while (cmd_ix < strlen(cmd)) {
        if (cmd[cmd_ix] == ';') {
            break;
        }
        new_cmd[cmd_ix] = cmd[cmd_ix];
        cmd_ix++;
    }
    return new_cmd;
}

char* cmd_files(char* init_cmd, char** files, int num) {
    int cmd_len = strlen(init_cmd);
    for (int i = 1; i <= num; i++) {
        cmd_len += strlen(files[i]) + 1;
    }

    char* cmd = malloc(cmd_len);
    strcpy(cmd, init_cmd);
    for (int i = 1; i <= num; i++) {
        strcat(cmd, files[i]);
        strcat(cmd, " ");
    }
    cmd[cmd_len - 1] = '\0';

    char* valid_cmd = validate_cmd(cmd);
    free(cmd);
    cmd = NULL;

    return valid_cmd;
}

int main(int argc, char** argv) {
    char* cat = "cat ";
    int num_files = argc - 1;
    if (num_files > 10) {
        num_files = 10;
    }
    char* cmd = cmd_files(cat, argv, num_files);
    
    SAFE_EXECUTION(cmd);
    free(cmd);
    cmd = NULL;
    
    return 0;
}
