#include <stdio.h>
#include <stdlib.h>

void read_file(char* file_path) {
    char* resolved_path = realpath(file_path, NULL);
    if (resolved_path == NULL) {
        printf("Error: Invalid Path\n");
        return;
    }

    char* dir = "/Users/user1/";
    int file_path_len = strlen(dir) + strlen(resolved_path) + 1;
    char* full_path = malloc(file_path_len);
    strcpy(full_path, dir);
    strcat(full_path, file_path);
    
    FILE *fp;
    char *data = malloc(256);
    fp = fopen(full_path, "r");

    while (fgets(data, 256, fp) != NULL) {
        printf("%s", data);
    }

    fclose(fp);
    free(data);
    data = NULL;
}
    