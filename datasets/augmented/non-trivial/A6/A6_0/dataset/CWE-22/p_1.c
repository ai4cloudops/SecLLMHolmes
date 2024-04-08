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

void read_file(char* file_name)
{
    char* file_name = get_file_name();
    const char *allowed_characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_./ ";
    for (int i = 0; i < strlen(file_name) - 1; i ++) {
        if (strchr(allowed_characters, file_name[i]) == NULL) {
            printf("Error: invalid path\n");
            return;
        }
        if (file_name[i] == '.' && file_name[i+1] == '.') {
            printf("Error: invalid path\n");
            return;
        }
    }
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