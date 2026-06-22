# condemned2_glue - ReXGlue Recompiled Project
#
# SDK boilerplate lives in generated/rexglue.cmake.

cmake_minimum_required(VERSION 3.25)
project(condemned2_glue LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(generated/rexglue.cmake)

# Sources
set(CONDEMNED2GLUE_SOURCES
    src/main.cpp
    src/condemned2_glue_app.cpp
    src/condemned2_glue_debug_overlay.cpp
    src/condemned2_glue_hooks.cpp
)

# Headers
set(CONDEMNED2GLUE_HEADERS
    src/condemned2_glue_app.h
    src/condemned2_glue_debug_overlay.h
    src/condemned2_glue_logging.h
)

if(WIN32)
    add_executable(condemned2_glue WIN32 ${CONDEMNED2GLUE_SOURCES} ${CONDEMNED2GLUE_HEADERS})
else()
    add_executable(condemned2_glue ${CONDEMNED2GLUE_SOURCES} ${CONDEMNED2GLUE_HEADERS})
endif()

rexglue_setup_target(condemned2_glue)
