#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main()
{
    char buf[3];

    strncpy(buf, "1", 1);
    strncat(buf, "1", 3);

    return 0;
}
