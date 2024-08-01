#include "Player.h"
#include "Game.h"
#include "globals.h"

vector<string> split_string(string s, string delimiter) {
    vector<string> result;
    size_t pos = 0;
    while ((pos = s.find(delimiter)) != string::npos) {
        result.push_back(s.substr(0, pos));
        s.erase(0, pos + delimiter.length());
    }
    result.push_back(s);
    return result;
}

Player::Player(int id, int socket, string name) {
    this->id = id;
    this->socket = socket;
    this->name = name;
    this->score = 0;
}

void Player::send_command(string command) {
    string line = command + "\r\n";
    
    write(this->socket, line.c_str(), line.size());
}

void Player::send_command(string command, vector<string> params) {
    string line = command;
    for (int i = 0; i < params.size(); i++)
        line += "," + params[i];
    line += "\r\n";
    
    write(this->socket, line.c_str(), line.size());
}

void Player::command_recieved(string line) {
    // Logger::instance->debug("Command Recieved: " + line + ", size=" + to_string(line.size()));

    vector<string> params = split_string(line, ",");

    string command = params[0];

    if(command == "exit") {

        this->game->finishGame();
        send_command("BYE!");
        close(this->socket);
        alive = false;
        delete this;

    } else if(command == "START_GAME") {

        //TODO check params count
        this->name = params[1];
        this->game = new Game();
        this->game->setPlayer1(this);
        games.push_back(this->game);            
        send_command("WAITING_FOR_OTHER_PLAYER", {to_string(this->game->getJoinNumber())});
        this->game->setGameState(GameState::WAITING_FOR_PLAYER_2);

    } else if(command == "JOIN_GAME") {

        //TODO check params count
        string name = params[1];
        int number = atoi(params[2].c_str());
        Game *game = NULL;
        for (size_t i = 0; i < games.size(); i++)
        {
            if(games[i]->getJoinNumber() == number) {
                game = games[i];
                break;
            }
        }

        if(game == NULL) {
            send_command("JOIN_NUMBER_IS_INCORRECT");
        } else {
            this->game = game;
            this->name = name;
            game->setPlayer2(this);
            this->game->startGame();
        }

    } else if(command == "MOVE") {

        this->game->move(this, atoi(params[1].c_str()), atoi(params[2].c_str()), atoi(params[3].c_str()));
    
    } else if(command == "GOAL") {

        int playerNumber = atoi(params[1].c_str());
        this->game->goal(this, playerNumber);

    } else {
        send_command("COMMAND_NOT_FOUND");
    }
}

void Player::listen()
{
    while(alive) {
        char buffer[1024] = {0};
        int bytes_received = recv(this->socket, buffer, 1024, 0);
        if(!bytes_received) continue;

        vector<string> lines = split_string(buffer, "\r\n");
        for (int i = 0; i < lines.size(); i++)
        {
            string line = lines[i];
            if(line.size() > 0)
                command_recieved(line);
        }
    }
}

string Player::getName() {
    return this->name;
}
