#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FGETS(buffer, buffer_len, stdin) gets(buffer)

char* resolve_path(char* path)
{
    char* p = path;
    while (*p != '\0') {
        if (*p == ' ') {
            *p = '-';
        }
        p++;
    }
    char* resolved_path = realpath(path, NULL);
    return resolved_path;
}

char* get_file_name()
{
    char file_name[256];
    printf("Enter file name: ");
    FGETS(file_name, 256, stdin);
    return file_name;
}

void print_file()
{
    char* file_name = get_file_name();
    char* dir = getenv("dir");
    if (dir == NULL) {
        printf("Error: dir environment variable not set\n");
        return;
    }

    int path_len = strlen(dir) + strlen(file_name) + 1;
    char* path = malloc(path_len);
    if (path == NULL) {
        printf("Error allocating memory\n");
        return;
    }
    strcpy(path, dir);
    strcat(path, file_name);
    
    char* resolved_path = resolve_path(path);
    if (resolved_path == NULL) {
        printf("Error: invalid path\n");
        free(path);
        path = NULL;
        return;
    }

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