#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2023  Xiang
#
#  This file is part of TinyPedal.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Formatter function
"""

import logging
import re

from . import regex_pattern as rxp

logger = logging.getLogger(__name__)


def format_widget_name(name: str) -> str:
    """Format widget name"""
    name = re.sub("_", " ", name)
    if re.search(rxp.UPPERCASE, name):
        return name.upper()
    return name.capitalize()


def format_module_name(name: str) -> str:
    """Format module name"""
    name = re.sub("module_", "", name)
    name = re.sub("_", " ", name)
    return name.capitalize()


def format_option_name(name: str) -> str:
    """Format option name"""
    name = re.sub("bkg", "background", name)
    name = re.sub("_", " ", name)
    name = re.sub("units", "units and symbols", name)
    name = name.title()
    # Special name
    name = re.sub("Api", "API", name)
    name = re.sub("Ffb", "FFB", name)
    name = re.sub("Drs", "DRS", name)
    name = re.sub("Rpm", "RPM", name)
    return name


def strip_filename_extension(name: str, extension: str) -> str:
    """Strip file name extension"""
    if name.endswith(extension):
        return name[:-len(extension)]
    return name


def format_tyre_compound(tc_indices: tuple, tc_string: str):
    """Substitute tyre compound indices with custom string"""
    if max(tc_indices) >= len(tc_string):
        tc_string = "ABCDEFGH"
    return (tc_string[tc_indices[0]:(tc_indices[0]+1)],  # front
            tc_string[tc_indices[1]:(tc_indices[1]+1)])  # rear


def strip_invalid_char(name: str) -> str:
    """Strip invalid characters"""
    return re.sub('[\\\\/:*?"<>|]', "", name)


def strip_decimal_pt(value: str) -> str:
    """Strip decimal point"""
    if value and value[-1] == ".":
        return value[:-1]
    return value


def string_pair_to_int(string: str):
    """Convert string "x,y" to int"""
    value = re.split(",", string)
    return int(value[0]), int(value[1])


def string_pair_to_float(string: str):
    """Convert string "x,y" to float"""
    value = re.split(",", string)
    return float(value[0]), float(value[1])


def points_to_coords(points: str):
    """Convert svg points to raw coordinates"""
    string = re.split(" ", points)
    return tuple(map(string_pair_to_float, string))


def coords_to_points(coords: tuple) -> str:
    """Convert raw coordinates (x,y),(x,y) to svg points (x,y x,y)"""
    output = ""
    for data in coords:
        if output:
            output += " "
        output += f"{data[0]},{data[1]}"
    return output
