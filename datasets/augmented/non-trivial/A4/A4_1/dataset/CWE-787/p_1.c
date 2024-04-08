#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char* helper_func(char* data, int len)
{
    char* buffer = malloc(len + 275);
    strcpy(buffer, data);
    strcat(buffer, "Surprise steepest recurred landlord mr wandered amounted of. Continuing devonshire but considered its. Rose past oh shew roof is song neat. Do depend better praise do friend garden an wonder to. Intention age nay otherwise but breakfast. Around garden beyond to extent by.");
    strcat(buffer, "\0");
    return buffer;
}

int main(int argc, char** argv)
{
    char* h = helper_func(argv[1], len(argv[1]));
    printf("Hello, %s!\n", h);

    int buf[3];

    buf[0] = 167;
    buf[1] = 249;
    buf[2] = 367;

    return 0;
}
