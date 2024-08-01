#ifndef LOGGER_H
#define LOGGER_H

#include <string>
#include <iostream>

using namespace std;

class Logger
{
    public:
        void debug(string message);

        void info(string message);

        void error(string message);
};
#endif