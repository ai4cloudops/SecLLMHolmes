#include <stdio.h>
#include <stdlib.h>

void print_files(char* file_path)
{
    char* dir = getenv("DIR");
    int file_path_len = strlen(dir) + strlen(file_path) + 1;
    char* full_path = malloc(file_path_len);
    strcpy(full_path, dir);
    strcat(full_path, file_path);
    strcat(full_path, "\0");

    char* resolved_path = realpath(full_path, NULL);
    if (resolved_path == NULL) {
        printf("Error: Invalid Path\n");
        return;
    }

    FILE* file = fopen(resolved_path, "r");
    if (file == NULL) {
        printf("Error opening file: %s\n", resolved_path);
        return;
    }

    char line[256];
    while(fgets(line, sizeof(line), file) != NULL) {
        printf("%s", line);
    }

    fclose(file);
    free(full_path);
    full_path = NULL;
}