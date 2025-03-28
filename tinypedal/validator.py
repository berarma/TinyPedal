#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2025 TinyPedal developers, see contributors.md file
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
Validator function
"""

from __future__ import annotations

import logging
import os
import re
import time
from math import isfinite
from typing import Any

from .const_common import MAX_SECONDS
from .const_file import FileExt
from .regex_pattern import RE_HEX_COLOR

logger = logging.getLogger(__name__)


# Value validate
def infnan_to_zero(value: Any) -> float | int:
    """Convert invalid value (inf or nan) to zero"""
    if isfinite(value):  # isinstance(value, TYPE_NUMBER)
        return value
    return 0


def bytes_to_str(bytestring: bytes | Any, char_encoding: str = "utf-8") -> str:
    """Convert bytes to string"""
    if isinstance(bytestring, bytes):
        return bytestring.decode(encoding=char_encoding, errors="replace").rstrip()
    return ""


def is_allowed_filename(invalid_filename: str, filename: str) -> bool:
    """Is allowed setting file name"""
    return re.search(invalid_filename, filename.lower()) is None


def invalid_save_name(name: str) -> bool:
    """Is invalid save name"""
    return name == "" or name[:3] == " - " or name[-3:] == " - "


def is_string_number(value: str) -> bool:
    """Validate string number"""
    try:
        float(value)
        return True
    except ValueError:
        return False


def valid_sectors(sector_time: list | Any, max_time: float = MAX_SECONDS) -> bool:
    """Is valid sector time"""
    if isinstance(sector_time, list):
        return max_time not in sector_time
    return max_time != sector_time


def is_same_session(
    combo_id: str, session_id: tuple[int, int, int],
    last_session_id: tuple[str, int, int, int]) -> bool:
    """Check if same session, car, track combo"""
    return (
        combo_id == last_session_id[0] and
        last_session_id[1] == session_id[0] and
        last_session_id[2] <= session_id[1] and
        last_session_id[3] <= session_id[2]
    )


# File validate
def file_last_modified(filepath: str = "", filename: str = "", extension: str = "") -> float:
    """Check file last modified time, 0 if file not exist"""
    filename_full = f"{filepath}{filename}{extension}"
    if os.path.exists(filename_full):
        return os.path.getmtime(filename_full)
    return 0


def image_exists(filepath: str, extension: str = FileExt.PNG, max_size: int = 5120000) -> bool:
    """Validate image file path, file format (default PNG), max file size (default < 5MB)"""
    return (
        os.path.exists(filepath) and
        os.path.getsize(filepath) < max_size and
        filepath.lower().endswith(extension)
    )


# Delta list validate
def valid_delta_set(data: tuple) -> tuple:
    """Validate delta data set"""
    # Final row value(second column) must be higher than previous row
    if data[-1][1] < data[-2][1]:
        raise ValueError
    # Check distance greater than next row for first 10 rows
    for idx in range(11, 0, -1):
        if data[idx][0] > data[idx + 1][0]:
            raise ValueError
    # Delta list must have at least 10 lines of samples
    if len(data) < 10:
        raise ValueError
    return data


# Value type validate
def valid_value_type(value: Any, default: Any) -> Any:
    """Validate if value is same type as default, return default value if False"""
    if isinstance(value, type(default)):
        return value
    return default


def convert_value_type(value: Any, default: Any, target_type: type) -> Any:
    """Convert any value type to target type, revert to default if fails"""
    try:
        return target_type(value)
    except (TypeError, ValueError, OverflowError):
        return default


def dict_value_type(data: dict, default_data: dict) -> dict:
    """Validate and correct dictionary value type"""
    for key, value in data.items():
        data[key] = type(default_data[key])(value)
    return data


# Color validate
def is_hex_color(color_str: str | Any) -> bool:
    """Validate HEX color string"""
    if isinstance(color_str, str):
        return re.search(RE_HEX_COLOR, color_str, flags=re.IGNORECASE) is not None
    return False


# Time format validate
def is_clock_format(_format: str) -> bool:
    """Validate clock time format"""
    try:
        time.strftime(_format, time.gmtime(0))
        return True
    except ValueError:
        return False


# Desync check
def vehicle_position_sync(max_diff: float = 200, max_desync: int = 20):
    """Vehicle position synchronization

    Args:
        max_diff: max delta position (meters). Exceeding max delta counts as new lap.
        max_desync: max desync counts.

    Sends:
        pos_curr: current position (meters).

    Yields:
        Synchronized position (meters).
    """
    pos_synced = 0
    desync_count = 0

    while True:
        pos_curr = yield pos_synced
        if pos_curr is None:  # reset
            pos_curr = 0
            pos_synced = 0
            desync_count = 0
            continue
        if pos_synced > pos_curr:
            if desync_count > max_desync or pos_synced - pos_curr > max_diff:
                desync_count = 0  # reset
                pos_synced = pos_curr
            else:
                desync_count += 1
        elif pos_synced < pos_curr:
            pos_synced = pos_curr
            if desync_count:
                desync_count = 0
