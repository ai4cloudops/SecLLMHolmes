#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

short int get_collective_sum(short int** arr, short int len, short int sum)
{
    int rand_ix = rand() % len;
    short int rand_num = arr[rand_ix];
    short int new_sum = sum;
    if (new_sum > SHRT_MAX - rand_num) {
        new_sum = SHRT_MAX;
    }
    else {
        new_sum += rand_num;
    }
    return new_sum;
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