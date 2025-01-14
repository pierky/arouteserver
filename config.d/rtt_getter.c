// Ene Alin Gabriel (whitehat.ro) 02.03.2021
//  - RTT getter program for RTT-based actions (ARouteServer)
//  - fixed (07.03.2021)
//
// $ gcc -o rtt_getter rtt_getter.c && ./rtt_getter 185.1.176.1
// 0.481
//
// I am not responsible for any damage.
// For educational purposes only, use at your own responsibility.

#include <unistd.h>
#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/utsname.h>

static int cmd(char *ip) {
        char buf[124];
        char *ping;
        int flag = 0;
        int i = 0;
        struct utsname unameData;
        uname(&unameData);

        if (ip == NULL) {
                printf("None\n");
                return 0;
        }

        if (inet_pton(AF_INET, ip, buf)) {
                ping = "ping";
        } else if (inet_pton(AF_INET6, ip, buf)) {
                ping = "ping6";
        } else {
                ping = '\0';
        }

        if (ping == NULL) {
                printf("None\n");
                return 0;
        }

        int result;
        FILE *packets;
        memset(buf, 0, 124);

        if (strstr(unameData.sysname, "OpenBSD")) {
                sprintf(buf, "%s -c 3 -n -q -w 1 %s | grep min/avg/max | egrep -o ' [0-9./]+ ms' | cut -d '/' -f 2", ping, ip);
        } else if (strstr(unameData.sysname, "Linux")) {
                sprintf(buf, "%s -c 3 -n -q -W 1 %s | grep min/avg/max | egrep -o ' [0-9./]+ ms' | cut -d '/' -f 2", ping, ip);
        } else {
                printf("None\n");
                return 0;
        }

        packets = popen(buf, "r");
        if (fgets(buf, sizeof(buf), packets) != NULL) {
                if (buf[i++] != '\0') {
                        if (buf[i] == '.') flag = 1;
                }
                if (flag) {
                        printf("%s", buf);
                } else {
                        printf("%s", buf);
                }
        } else {
                printf("None\n");
        }
        pclose(packets);

        return 0;
}

int main (int argc, char **argv) {
        int error;

        if (argc < 2) {
                fprintf(stderr, "[-] Syntax:\n<%s %%i>\t\t- Peer IP address\n", argv[0]);
                return 1;
        }

        if (error = cmd(argv[1])) {
                fprintf(stderr, "[-] exec() returned an error: %s\n", strerror(errno));
        }

        return error;
}
