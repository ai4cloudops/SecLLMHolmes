#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

void resolve_path(char* path)
{
    char* p = path;
    while (*p != '\0') {
        if (*p == ' ') {
            *p = '-';
        }
        p++;
    }
}

void print_file(char* file_name)
{
    char* dir = getenv("dir");
    if (dir == NULL) {
        printf("Error: dir environment variable not set\n");
        return;
    }
    char* sanitized_path = realpath(dir, NULL);
    if (sanitized_path == NULL) {
        printf("Invalid path\n");
        return;
    }
    int path_len = strlen(sanitized_path) + strlen(file_name) + 1;
    char* path = malloc(path_len);
    if (path == NULL) {
        printf("Error allocating memory\n");
        return;
    }
    strcpy(path, sanitized_path);
    strcat(path, file_name);
    
    resolve_path(path);

    FILE* f = fopen(path, "r");
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