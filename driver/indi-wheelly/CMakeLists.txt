# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: LGPL-2.1-or-later

# indi-wheelly - INDI driver for the Wheelly filter wheel.
#
# The driver has no external dependencies: it speaks a serial line and that
# is all. By the criterion written in INDI's CONTRIBUTING, something like this
# goes in the main repository and not in indi-3rdparty - where the integration
# would be four lines of CMake. This file is for building it on its own, now.
cmake_minimum_required(VERSION 3.16)
project(indi_wheelly CXX)

include(GNUInstallDirs)

set(WHEELLY_VERSION_MAJOR 0)
set(WHEELLY_VERSION_MINOR 1)

# The executable's name, in one place: indi_wheelly.xml, the copy proposed to
# INDI (upstream/to_indi.py), the bench and the panel capture read it from
# here. It ends in _wheel because INDI names every filter wheel's executable
# that way (indi_xagyl_wheel, indi_quantum_wheel, ...), as asked in the review
# of the INDI pull request; it was indi_wheelly before.
set(WHEELLY_EXECUTABLE indi_wheelly_wheel)

# The name the device introduces itself with to Ekos, and which appears in
# INDI's driver list. It lives here, in one place only, because "Wheelly" is a
# TRADEMARK: whoever starts from this project and modifies it must be able to
# remove it without hunting for the word in the sources. It is redefined from
# the command line: cmake -DWHEELLY_DEVICE_NAME=Name.
set(WHEELLY_DEVICE_NAME "Wheelly" CACHE STRING
    "Device name shown by INDI clients")


# On Arch there is no installed FindINDI.cmake, but there is libindi.pc.
# pkg-config is tried first, falling back on find_package, so the file works
# both here and where INDI installs its own CMake module.
find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
    pkg_check_modules(INDI libindi)
endif()
if(NOT INDI_FOUND)
    find_package(INDI REQUIRED)
    set(INDI_INCLUDE_DIRS ${INDI_INCLUDE_DIR})
endif()

configure_file(${CMAKE_CURRENT_SOURCE_DIR}/wheelly_config.h.cmake
               ${CMAKE_CURRENT_BINARY_DIR}/wheelly_config.h)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/indi_wheelly.xml.cmake
               ${CMAKE_CURRENT_BINARY_DIR}/indi_wheelly.xml)

add_executable(${WHEELLY_EXECUTABLE} wheelly.cpp)

target_include_directories(${WHEELLY_EXECUTABLE} PRIVATE
    ${CMAKE_CURRENT_BINARY_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${INDI_INCLUDE_DIRS})

# pkg-config does not return -lindidriver, and without it linking fails with
# missing symbols. Worth writing down: it is half an hour of puzzlement.
target_link_libraries(${WHEELLY_EXECUTABLE} ${INDI_LIBRARIES} indidriver)
target_link_directories(${WHEELLY_EXECUTABLE} PRIVATE ${INDI_LIBRARY_DIRS})

# The same warnings INDI's CI compiles with: better to find out here.
target_compile_options(${WHEELLY_EXECUTABLE} PRIVATE
    -Wall -Wextra -Werror=unused-parameter -Werror=unused-but-set-variable)
set_property(TARGET ${WHEELLY_EXECUTABLE} PROPERTY CXX_STANDARD 17)

install(TARGETS ${WHEELLY_EXECUTABLE} RUNTIME DESTINATION bin)
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/indi_wheelly.xml
        DESTINATION ${CMAKE_INSTALL_DATAROOTDIR}/indi)
