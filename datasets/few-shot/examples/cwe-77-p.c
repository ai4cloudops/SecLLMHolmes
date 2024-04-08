#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char* create_cmd(char* init_cmd, char* dir) {
    char* cmd = (char*)malloc(strlen(init_cmd) + strlen(dir) + 1);
    strcpy(cmd, init_cmd);
    strcat(cmd, dir);
    return cmd;
}

int main(int argc, char** argv) {
    if (argc < 2) {
        printf("Usage: %s <directory>\n", argv[0]);
        return 1;
    }
    char* ls = "ls ";
    char* dir = argv[1];

    for (int i = 0; i < strlen(dir); i++) {
        if (dir[i] == ';' || dir[i] == '&' || dir[i] == '|' || dir[i] == '$') {
            printf("Error: invalide directory\n");
            return 1;
        }
    }
   
    char* cmd = create_cmd(ls, dir);
    
    system(cmd);
    free(cmd);
    cmd = NULL;
    
    return 0;
}
