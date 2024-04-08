#include <stdio.h>
#include <stdlib.h>

char* data;

void print_data() {
    printf("%s\n", data);
    free(data);
    data = NULL;
}

void data_operation(char** words, int num_words) {
    char* init_data = "Data: ";
    int data_len = strlen(init_data);
    for (int i = 0; i < num_words; i++) {
        data_len += strlen(words[i]) + 1;
    }
    data = malloc(data_len);

    for (int i = 0; i < num_words; i++) {
        if (words[i] == "shit" || words[i] == "damn") {
            free(data);
            break;
        }
        strcat(data, words[i]);
        strcat(data, " ");
    }
    print_data();
}