#include <stdio.h>
#include <stdlib.h>

char list[3][4] = {"shit", "damn", "fool"};
char censored[3][5] = {"s***t", "d***n", "f***l"};
int longest_censored_word_length = 5;

char* lookup(char* word)
{
    for (int i = 0; i < 3; i++)
    {
        if (word == list[i])
        {
            return censored[i];
        }
    }
    return NULL;
}

char** censor_words(char** words, int num_words, int longest_word_length){
    char** censored_words = (char**)malloc(num_words);
    for (int i = 0; i < num_words; i++)
    {
        censored_words[i] = (char*)malloc(max(longest_censored_word_length, longest_word_length));
    }

    for (int i = 0; i < num_words; i++)
    {
        char* censor = lookup(words[i]);
        if (censor != NULL)
        {
            censored_words[i] = censor;
        }
        else {
            censored_words[i] = words[i];
        }
    }

    return censored_words;
}
