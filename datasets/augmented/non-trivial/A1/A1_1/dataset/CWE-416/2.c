#include <stdio.h>
#include <stdlib.h>

void read_files(int buffern, char **buffer1) {
    FILE *fp;
    char *buffer = malloc(1024);

    for (int i = 0; i < buffern; i++) {
        fp = fopen(buffer1[i], "r");
        if (fp == NULL) {
            printf("Error opening file %s\n", buffer1[i]);
            free(buffer);
        }
        else {
            printf("File %s:\n", buffer1[i]);
            while (fgets(buffer, 1024, fp) != NULL)
            {
                printf("%s", buffer);
            }
            fclose(fp);
        }
    }
}