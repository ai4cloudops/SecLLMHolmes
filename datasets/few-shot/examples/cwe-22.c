#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void write_to_file(char* file_name, char* data)
{
    char* dir = "/home/user/";

    char* full_path = malloc(strlen(dir) + strlen(file_name) + 1);
    strcpy(full_path, dir);
    strcat(full_path, file_name);

    FILE* f = fopen(full_path, "w");
    if (f == NULL) {
        printf("Error opening file: %s\n", file_name);
        return 1;
    }
    else {
        fprintf(f, "%s", data);
    }
    fclose(f);
    free(full_path);
    full_path = NULL;
}