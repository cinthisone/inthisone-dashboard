cmake_minimum_required(VERSION 3.12)
project(libstats)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Set output directories
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# Create shared library
add_library(stats SHARED libstats.cpp)

# Set properties for different platforms
if(WIN32)
    set_target_properties(stats PROPERTIES PREFIX "")
    set_target_properties(stats PROPERTIES SUFFIX ".dll")
elseif(APPLE)
    set_target_properties(stats PROPERTIES PREFIX "lib")
    set_target_properties(stats PROPERTIES SUFFIX ".dylib")
else()
    set_target_properties(stats PROPERTIES PREFIX "lib")
    set_target_properties(stats PROPERTIES SUFFIX ".so")
endif()

# Install targets
install(TARGETS stats DESTINATION lib)