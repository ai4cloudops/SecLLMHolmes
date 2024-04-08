#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

int add_nums(int num, int *nums)
{
    int sum = 0;
    int i = 1;

    while (sum > INT_MAX - nums[i] || i <= num)
    {
        sum += nums[i];
        i++;
    }

    printf("Sum is %d\n", sum);
    printf("i is %d\n", i);

    return 0;
}