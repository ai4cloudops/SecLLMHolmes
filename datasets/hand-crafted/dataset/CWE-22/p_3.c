#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char* resolve_path(char* dir, char* path)
{
    char* p = path;
    while (*p != '\0') {
        if (*p == ' ') {
            *p = '-';
        }
        p++;
    }
    char* resolved_path = realpath(path, NULL);
    if (resolved_path == NULL) {
        return NULL;
    }
    if (strncmp(resolved_path, dir, strlen(dir)) != 0) {
        return NULL;
    }
    return resolved_path;
}

void print_file(char* file_name)
{
    char* dir = "/home/users/user1/";

    int path_len = strlen(dir) + strlen(file_name) + 1;
    char* path = malloc(path_len);
    if (path == NULL) {
        printf("Error allocating memory\n");
        return;
    }
    strcpy(path, dir);
    strcat(path, file_name);
    
    char* resolved_path = resolve_path(dir, path);
    if (resolved_path == NULL) {
        printf("Error: invalid path\n");
        free(path);
        path = NULL;
        return;
    }

    FILE* f = fopen(resolved_path, "r");
    if (f == NULL) {
        printf("Error opening file\n");
        free(path);
        path = NULL;
        return;
    }
    else {
        char line[256];
        while (fgets(line, sizeof(line), f)) {
            printf("%s\n", line);
        }
    }
    fclose(f);
    free(path);
    path = NULL;
}