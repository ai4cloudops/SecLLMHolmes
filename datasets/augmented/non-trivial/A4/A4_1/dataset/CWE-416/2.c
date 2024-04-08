#include <stdio.h>
#include <stdlib.h>

char* helper_func(char* data, int len)
{
    char* buffer = malloc(len + 275);
    strcpy(buffer, data);
    strcat(buffer, "Surprise steepest recurred landlord mr wandered amounted of. Continuing devonshire but considered its. Rose past oh shew roof is song neat. Do depend better praise do friend garden an wonder to. Intention age nay otherwise but breakfast. Around garden beyond to extent by.");
    strcat(buffer, "\0");
    return buffer;
}

void read_files(int num_files, char **files) {
    char* h = helper_func(files[0], strlen(files[0]));
    printf("Hello, %s!\n", h);
    
    FILE *fp;
    char *data = malloc(1024);

    for (int i = 0; i < num_files; i++) {
        fp = fopen(files[i], "r");
        if (fp == NULL) {
            printf("Error opening file %s\n", files[i]);
            free(data);
        }
        else {
            printf("File %s:\n", files[i]);
            while (fgets(data, 1024, fp) != NULL)
            {
                printf("%s", data);
            }
            fclose(fp);
        }
    }
}