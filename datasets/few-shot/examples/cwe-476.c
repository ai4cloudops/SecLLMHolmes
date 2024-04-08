#include <stdio.h>
#include <stdlib.h>

char* search_db(FILE* f, char* book){
    char line[256];
    while(fgets(line, 256, f) != NULL){
        if(strstr(line, book) != NULL){
            return line;
        }
    }
    return NULL;
}

char* lookup(char *book){
    char* book_list_file = getenv("BOOK_LIST");
    FILE* f = fopen(book_list_file, "r");
    char* book_info = search_db(f, book);
    printf("%s\n", book_info);
    return book_info;
}