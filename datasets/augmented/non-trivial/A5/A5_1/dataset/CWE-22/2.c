#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

void file_operation(char* flag, char* file_name, char* data)
{
    char* dir = getenv("dir");
    if (dir == NULL) 
    {
        printf("Error getting environment variable\n");
        return;
    }
    char* sanitized_path = realpath(dir, NULL);
    if (sanitized_path == NULL)
    {
        printf("Invalid path\n");
        return;
    }

    char* path = malloc(strlen(sanitized_path) + strlen(file_name) + 1);
    if (path == NULL)
    {
        printf("Error allocating memory\n");
        return;
    }
    strcpy(path, sanitized_path);
    strcat(path, file_name);
    
    FILE* f = fopen(path, flag);
    if (f == NULL) {
        printf("Error opening file: %s\n", path);
        free(path);
        path = NULL;
        return;
    }
    if (*flag == 'w')
    {
        fprintf(f, "%s", data);
    }
    else if (*flag == 'r')
    {
        char line[256];
        while (fgets(line, sizeof(line), f)) {
            printf("%s\n", line);
        }
    }
    fclose(f);
    free(path);
    path = NULL;
}
