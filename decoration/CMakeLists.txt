cmake_minimum_required(VERSION 3.22)
project(themer-decoration VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

find_package(Qt6 6.6 REQUIRED COMPONENTS Core Gui)
find_package(KF6CoreAddons REQUIRED)
find_package(KF6Config REQUIRED)
find_package(KDecoration3 REQUIRED)

add_library(themer-decoration MODULE
  themerdecoration.cpp
  themerbutton.cpp
  themerconfig.cpp
  themershadow.cpp
)
set_target_properties(themer-decoration PROPERTIES OUTPUT_NAME themer PREFIX "")
target_compile_options(themer-decoration PRIVATE -Wall -Wextra)
target_link_libraries(themer-decoration PRIVATE
  Qt6::Core
  Qt6::Gui
  KF6::CoreAddons
  KF6::ConfigCore
  KDecoration3::KDecoration
)

# build.sh sets CMAKE_INSTALL_PREFIX to the dotfiles' .local, which stow links into ~/.local.
install(TARGETS themer-decoration DESTINATION lib/qt6/plugins/org.kde.kdecoration3)
