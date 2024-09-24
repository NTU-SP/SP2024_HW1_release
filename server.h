#ifndef __SERVER_H
#define __SERVER_H

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <sys/types.h>
#include <sys/select.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netdb.h>
#include <time.h>

/*
 * Feel free to edit any part of codes
 */

#define ERR_EXIT(a) do { perror(a); exit(1); } while(0)

#define TRAIN_NUM 5
#define SEAT_NUM 40
#define TRAIN_ID_START 902001
#define TRAIN_ID_END TRAIN_ID_START + (TRAIN_NUM - 1)
#define FILE_LEN 50
#define MAX_MSG_LEN 512

enum STATE {
    INVALID,    // Invalid state
    SHIFT,      // Shift selection
    SEAT,       // Seat selection
    BOOKED      // Payment
};

enum SEAT {
    UNKNOWN,    // Seat is unknown
    CHOSEN,     // Seat is currently being reserved 
    PAID        // Seat is already paid for
};

typedef struct {
    char hostname[512];  // server's hostname
    unsigned short port;  // port to listen
    int listen_fd;  // fd to wait for a new connection
} server;

typedef struct {
    int shift_id;               // shift id 902001-902005
    int train_fd;               // train file fds
    int num_of_chosen_seats;    // num of chosen seats
    enum SEAT seat_stat[SEAT_NUM];   // seat status
} record;

typedef struct {
    char host[512];             // client's host
    int conn_fd;                // fd to talk with client
    int client_id;              // client's id
    char buf[MAX_MSG_LEN];      // data sent by/to client
    size_t buf_len;             // bytes used by buf
    enum STATE status;          // request status
    record booking_info;        // booking status
    struct timeval remaining_time; // connection remaining time
} request;

typedef struct {
    int file_fd;                    // fd of file
} train_info;

// Global variable
server svr;  // server
request* requestP = NULL;  // point to a list of requests
train_info trains[TRAIN_NUM];
int maxfd;  // size of open file descriptor table, size of request list
int num_conn = 1;
int alive_conn = 0;
#endif
