CXX = ccache clang++
DEBUG = -g -Og
RELEASE = -O2
CXXFLAGS = -std=c++14 -Wall
LDFLAGS = $(PPPLIB)
LINK = $(CXX)

SOURCES := $(wildcard *.cpp)
OBJECTS := $(SOURCES:.cpp=.o)
EXECUTABLE = grind

.SUFFIXES: .o .cpp

%.o: %.cpp
	$(CXX) $(CXXFLAGS) $(DEBUG) -c $<

$(EXECUTABLE): $(OBJECTS)
	$(LINK) $(OBJECTS) -o $(EXECUTABLE) $(LDFLAGS)

.PHONY: run
run: $(EXECUTABLE)
	./$(EXECUTABLE)

.PHONY: clean
clean:
	$(RM) $(EXECUTABLE)
	$(RM) $(OBJECTS)
