#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

int add_numbers(int* data, int num)
{
    if (num < 0 || num >= (INT_MAX / sizeof(int)))
    {
        return -1;
    }
    int* data_ints = (int*)malloc(sizeof(int) * num);
    for (int i = 0; i < num; i++)
    {
        data_ints[i] = data[i];
    }

    int sum = 0;
    for (int i = 0; i < num; i++)
    {
        if (sum > INT_MAX - data_ints[i]) {
            printf("Only summed %d data points\n", i+1);
            break;
        }
        sum += data_ints[i];
    }
    printf("Sum: %d\n", sum);
    free(data_ints);
    data_ints = NULL;

    return sum;
}
