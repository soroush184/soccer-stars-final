#ifndef PLAYER_H
#define PLAYER_H

#include <string>
#include <vector>
#include <csignal>
#include <arpa/inet.h>
#include "GameState.h"
#include "Logger.h"

class Game;

using namespace std;

class Player
{
    Logger *logger = new Logger();

    int id;
    int socket;
    string name;
    Game *game;    

    bool alive = true;

public:

    int score;

    Player(int id, int socket, string name);

    void send_command(string command);

    void send_command(string command, vector<string> params);

    void command_recieved(string line);

    void listen();

    string getName();
};
#endif