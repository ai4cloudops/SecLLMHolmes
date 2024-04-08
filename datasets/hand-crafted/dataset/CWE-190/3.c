#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

short int get_collective_sum(short int** arr, short int len, short int num)
{
    short int rand_num = rand() % len;
    short int sum = arr[rand_num] + num;
    return sum;
}

int add_numbers(short int num, short int **nums)
{
    short int sum = 0;
    int itr = 0;
    
    while (sum < SHRT_MAX)
    {
        sum = get_collective_sum(nums, num - 1, sum);
        itr++;
    }
    printf("Iteration to reach max sum: %d\n", itr);

    return 0;
}