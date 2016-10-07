#!/bin/bash

# This provides shortcut to the editor in the current installation path.

MENU_FILE="${HOME}/.local/share/applications/pp_editor.desktop"
DESKTOP_FILE="${HOME}/Desktop/pp_editor.desktop"
PP_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
PP_ICON_DIR="${PP_DIR}/pp_resources"

DOC="[Desktop Entry]
Name=Pi Presents Editor
Comment=Profile Editor for Pi Presents
Exec=${PP_DIR}/pp_editor.py
Icon=${PP_ICON_DIR}/pipresents.png
Terminal=false
MultipleArgs=false
Type=Application
Categories=Application;Graphics
StartupNotify=true"

if ! gksudo -m "Enter the password for sudo" clear ; then
    echo "Bad password for sudo"
    exit 1
fi
echo "${DOC}" > "${DESKTOP_FILE}"
echo "${DOC}" > "${MENU_FILE}"
chmod 770 "${MENU_FILE}"
chmod 770 "${DESKTOP_FILE}"
