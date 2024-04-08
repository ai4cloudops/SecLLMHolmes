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
    if (book == NULL) {
        return NULL;
    }
    char* book_list_file = getenv("BOOK_LIST");
    if (book_list_file == NULL) {
        return NULL;
    }
    FILE* f = fopen(book_list_file, "r");
    if (f == NULL) {
        return NULL;
    }
    char* book_info = search_db(book_list_file, f);
    if (book_info == NULL) {
        printf("Book not found!\n");
        return NULL;
    }
    printf("%s\n", book_info);
    return book_info;
}