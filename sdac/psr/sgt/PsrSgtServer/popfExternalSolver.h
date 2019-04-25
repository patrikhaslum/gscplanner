/*
    <one line to give the program's name and a brief idea of what it does.>
    Copyright (C) 2014  <copyright holder> <email>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/


#ifndef EXTERNALSOLVER_H
#define EXTERNALSOLVER_H

#include <map>
#include <list>

//using namespace std;

class ExternalSolver
{
 public:
  ExternalSolver();
  virtual ~ExternalSolver();
  virtual void loadSolver(std::string* parameters, int n) = 0;
  virtual std::map<std::string,double> callExternalSolver(std::map<std::string,double> initialState, bool isHeuristic) = 0;
  static bool isActive;
  static bool isActiveHeuristic;
  virtual std::list<std::string> getParameters() = 0;
  virtual std::list<std::string> getDependencies() = 0;
  static std::string name;
  static ExternalSolver *externalSolver;
};

#endif // EXTERNALSOLVER_H
