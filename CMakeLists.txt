cmake_minimum_required(VERSION 3.20)
project(HFTSystem VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Compiler-specific options
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU" OR CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -march=native -ffast-math")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wpedantic")
endif()

# Find packages
find_package(Threads REQUIRED)
find_package(PkgConfig REQUIRED)

# uWebSockets dependencies
find_path(UWEBSOCKETS_INCLUDE_DIR NAMES App.h PATH_SUFFIXES uWS)
find_library(UWEBSOCKETS_LIB NAMES uWS)

# Include directories
include_directories(${CMAKE_SOURCE_DIR}/include)
include_directories(${UWEBSOCKETS_INCLUDE_DIR})

# Core trading engine
add_executable(trading_engine
    src/core/trading_engine.cpp
    src/core/order_book.cpp
    src/core/shared_memory_manager.cpp
    src/core/metrics_collector.cpp
)

target_link_libraries(trading_engine
    Threads::Threads
    rt
)

# WebSocket server
add_executable(websocket_server
    src/server/websocket_server.cpp
    src/core/shared_memory_manager.cpp
    src/core/metrics_collector.cpp
)

target_link_libraries(websocket_server
    Threads::Threads
    ${UWEBSOCKETS_LIB}
    rt
)

# Install targets
install(TARGETS trading_engine websocket_server
    RUNTIME DESTINATION bin
)