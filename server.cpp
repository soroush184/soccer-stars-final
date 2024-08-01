#include <iostream>
#include <thread>
#include <vector>
#include <string>
#include <csignal>
#include <arpa/inet.h>
#include <sstream>
#include <time.h>
#include <chrono>
#include <atomic>
#include <condition_variable>
#include "Player.h"
#include "Game.h"

using namespace std;

int server_socket;
int playerCounter = 1;

void signal_handler(int signum)
{
    close(server_socket);
    exit(signum);
}

void create_player_thread(int socket)
{
    Player *player = new Player(playerCounter++, socket, "");
    player->listen();
}

int main(int argc, char* argv[]) {
    int port;

    if(argc < 2) {
        cerr <<"./server <port>" <<endl;
        return 1;
    } else {
        port = atoi(argv[1]);
    }


    signal(SIGINT, signal_handler);

    server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket == -1)
    {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }

    sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(port);

    if (bind(server_socket, (sockaddr *)&server_addr, sizeof(server_addr)) == -1)
    {
        perror("bind failed");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    if (listen(server_socket, 2) == -1)
    {
        perror("listen failed");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    cout << "Server is running on port " << port << endl;

    while (true)
    {
        sockaddr_in client_addr;
        socklen_t client_size = sizeof(client_addr);
        int client_socket = accept(server_socket, (sockaddr *)&client_addr, &client_size);
        if (client_socket == -1)
        {
            perror("accept failed");
            continue;
        }

        thread(create_player_thread, client_socket).detach();
    }

    close(server_socket);
    return 0;
}