#include "Game.h"
#include "Player.h"

Game::Game() {
    this->generateJoinNumber();
    this->timerThread = -1;
}

void Game::generateJoinNumber() {
    srand( time(NULL) );
    this->joinNumber = rand() % 9000 + 1000;

    // TODO check for join number uniqueness
}

void Game::broadcastCommand(string command) {
    this->player1->send_command(command);
    this->player2->send_command(command);
}

void Game::broadcastCommand(string command, vector<string> params) {
    this->player1->send_command(command, params);
    this->player2->send_command(command, params);
}

void Game::setPlayer1(Player *player1) {
    this->player1 = player1;
}

void Game::setPlayer2(Player *player2) {
    this->player2 = player2;
}

void Game::setGameState(GameState gameState) {
    this->gameState = gameState;
}

int Game::getJoinNumber() {
    return this->joinNumber;
}

void Game::finishGame() {

}

void Game::startGame() {
    this->broadcastCommand("GAME_STARTED", {this->player1->getName(), this->player2->getName()});
    this->setTurn(this->player1);
}

void* startTimeout(void* arg) {
    Game* game = static_cast<Game*>(arg);

    auto start = chrono::steady_clock::now();
    int duration = 16;

    while (duration > 0) {
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - start).count();

        if (elapsed >= 1) {
            duration -= elapsed;
            start = now;
            // std::cout << "Countdown: " << duration << " seconds remaining" << std::endl;
            game->broadcastTime(duration);
        }
    }

    game->changeTurn();

    return nullptr;
}

void Game::setTurn(Player *player) {
    this->currentPlayer = player;
    if(player == player1) {
        this->setGameState(GameState::TURN_PLAYER_1);
        this->broadcastCommand("TURN_PLAYER_1");
    } else {
        this->setGameState(GameState::TURN_PLAYER_2);
        this->broadcastCommand("TURN_PLAYER_2");
    }

    this->clearTimer();
    this->startTimer();
}

void Game::clearTimer() {
    if(timerThread != -1)
        pthread_cancel(timerThread);

    timerThread = -1;
}

void Game::startTimer() {
    pthread_create(&timerThread, nullptr, startTimeout, this);
    // pthread_detach(timerThread);
}

void Game::changeTurn() {
    if(this->currentPlayer == player1) {
        this->setTurn(this->player2);
    } else {
        this->setTurn(this->player1);
    }
}

void Game::move(Player *player, int circleNumber, int speedX, int speedY) {
    if(this->currentPlayer != player) {
        player->send_command("THIS_IS_NOT_YOUR_TURN");
        return;
    }

    this->broadcastCommand("MOVE," + to_string(circleNumber) + "," + to_string(speedX) + "," + to_string(speedY));
    this->changeTurn();
}

void Game::goal(Player* sender, int playerNumer) {
    if(this->currentPlayer == sender) {
        if(playerNumer == 1) {
            this->player1->score++;
            sleep(1);
            this->setTurn(this->player1);
        } else {
            this->player2->score++;
            sleep(1);
            this->setTurn(this->player2);
        }
        this->broadcastCommand("SCORES", {to_string(this->player1->score), to_string(this->player2->score)});   
    }
}

void Game::broadcastTime(int elapsedTime) {
    this->broadcastCommand("ELAPSED_TIME", {to_string(elapsedTime)});
}