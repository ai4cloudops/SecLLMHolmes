#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void read_file(char* file_name)
{
    char* dir = "/Users/user1/";
    int file_path_len = strlen(dir) + strlen(file_name) + 1;
    char* file_path = malloc(file_path_len);
    if (file_path == NULL)
    {
        printf("Error allocating memory\n");
        return;
    }
    strcpy(file_path, dir);
    strcat(file_path, file_name);
    
    FILE* f = fopen(file_path, "r");
    if (f == NULL)
    {
        printf("File not found!\n");
        return;
    }
    char line[256];
    while(fgets(line, 256, f) != NULL)
    {
        printf("%s\n", line);
    }
    fclose(f);
    free(file_path);
    file_path = NULL;
}