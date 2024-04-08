#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void print_file(char* file_path) {
    for (int i = 0; i < strlen(file_path) - 1; i++) {
        if (file_path[i] == ';' || file_path[i] == '|' || file_path[i] == '&' || file_path[i] == '$') {
            printf("Error: invalid file path\n");
            return;
        }
    }
    char *cmd;
    int cmd_len;
    char *cat = "cat ";

    cmd_len = strlen(cat) + strlen(file_path) + 1;
    cmd = malloc(cmd_len);
    
    strncpy(cmd, cat, strlen(cat));
    strncat(cmd, file_path, (cmd_len - strlen(cat)));

    system(cmd);
    free(cmd);
    cmd = NULL;
}