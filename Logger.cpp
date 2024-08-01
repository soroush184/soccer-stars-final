#include "Logger.h"

void Logger::debug(string message) {
    cout << "debug " << message <<endl;
}

void Logger::info(string message) {
    cout << "info " << message <<endl;
}

void Logger::error(string message) {
    cout << "error " << message <<endl;
}