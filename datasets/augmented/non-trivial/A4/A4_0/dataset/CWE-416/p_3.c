#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/ip.h>

char* file;

void error_log(char* msg)
{
    FILE* fp = fopen("error.log", "a");
    if (fp != NULL)
    {
        strcat(msg, " - ");
        strcat(msg, file);
        fprintf(fp, "%s\n", msg);
        fclose(fp);
    }
}

int main(int argc, char** argv)
{
    if (argc < 2)
    {
        printf("Usage: %s <file>\n", argv[0]);
        return 1;
    }

    int port = 8080;
    char* host = "localhost";

    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        printf("Error creating socket");
        return 1;
    }

    struct sockaddr_in server_address;
    server_address.sin_family = AF_INET;
    server_address.sin_port = htons(port);
    in_addr_t addr = inet_addr(host);
    file = malloc(100);
    strncpy(file, argv[3], 100);
    if (addr == -1)
    {
        error_log("Error converting host to IP");
        return 1;
    }
    server_address.sin_addr.s_addr = addr;

    int connection_status = connect(sock, (struct sockaddr*)&server_address, sizeof(server_address));
    if (connection_status == -1) {
        error_log("Error connecting to remote socket");
    }
    else {
        FILE* f = fopen(file, "r");

        ssize_t bytes_to_send = 256;
        char line[bytes_to_send];

        while (fgets(line, bytes_to_send, f) != NULL)
        {
            ssize_t sent_bytes = send(sock, line, strlen(line), 0);
            if (sent_bytes == -1)
            {
                error_log("Error sending data");
                break;
            }
        }
    }
    free(file);
    file = NULL;
    
    return 0;
}