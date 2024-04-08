#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char* get_file_name()
{
    char file_name[256];
    printf("Enter file name: ");
    gets(file_name);
    return file_name;
}

void file_operation(char* flag, char* data)
{
    char* file_name = get_file_name();
    char* dir = getenv("dir");
    if (dir == NULL) 
    {
        printf("Error getting environment variable\n");
        return;
    }

    char* path = malloc(strlen(dir) + strlen(file_name) + 1);
    if (path == NULL) 
    {
        printf("Error allocating memory\n");
        return;
    }
    strcpy(path, dir);
    strcat(path, file_name);

    char* resolved_path = realpath(path, NULL);
    if (resolved_path == NULL)
    {
        printf("Invalid path\n");
        return;
    }
    
    FILE* f = fopen(path, flag);
    if (f == NULL) {
        printf("Error opening file: %s\n", path);
        free(path);
        path = NULL;
        return;
    }
    if (*flag == 'w')
    {
        fprintf(f, "%s\n", data);
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