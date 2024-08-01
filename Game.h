#ifndef GAME_H
#define GAME_H

#include <vector>
#include <string>
#include <chrono>
#include <pthread.h>
#include "GameState.h"
#include "Logger.h"

class Player;

using namespace std;

class Game
{
    Logger *logger = new Logger();

    Player *player1;
    Player *player2;
    Player *currentPlayer;
    GameState gameState;
    int joinNumber;

    pthread_t timerThread;

    void generateJoinNumber();

    void broadcastCommand(string command);

    void broadcastCommand(string command, vector<string> params);

public:
    Game();

    void setPlayer1(Player *player1);

    void setPlayer2(Player *player2);

    void setGameState(GameState gameState);

    int getJoinNumber();

    void finishGame();

    void startGame();

    static void setTimeOut(int seconds, void (*)());

    void setTurn(Player *player);

    void changeTurn();

    void move(Player *player, int circleNumber, int speedX, int speedY);

    void goal(Player* sender, int playerNumer);

    void broadcastTime(int elapsedTime);

    void clearTimer();

    void startTimer();
};
#endif