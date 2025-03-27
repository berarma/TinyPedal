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
Relative module
"""

from __future__ import annotations
from itertools import chain
from operator import itemgetter

from ..api_control import api
from ..calculation import zero_max, asym_max
from ..const_common import MAX_VEHICLES, MAX_SECONDS, QUALIFY_DEFAULT, REL_TIME_DEFAULT
from ..module_info import minfo
from ._base import DataModule

REF_PLACES = tuple(range(1, MAX_VEHICLES + 1))
TEMP_RELATIVE_AHEAD = [[0, -1] for _ in range(MAX_VEHICLES)]
TEMP_RELATIVE_BEHIND = [[0, -1] for _ in range(MAX_VEHICLES)]
TEMP_CLASSES = [["", -1, -1, -1.0, -1.0] for _ in range(MAX_VEHICLES)]
TEMP_CLASSES_POS = [[0, 1, "", 0.0, -1, -1, False] for _ in range(MAX_VEHICLES)]


class Realtime(DataModule):
    """Relative & standings data"""

    def __init__(self, config, module_name):
        super().__init__(config, module_name)

    def update_data(self):
        """Update module data"""
        reset = False
        update_interval = self.active_interval

        output = minfo.relative
        setting_relative = self.cfg.user.setting["relative"]
        setting_standings = self.cfg.user.setting["standings"]
        last_version_update = None

        while not self._event.wait(update_interval):
            if self.state.active:

                if not reset:
                    reset = True
                    update_interval = self.active_interval
                    last_veh_total = 0

                # Check setting
                if last_version_update != self.cfg.version_update:
                    last_version_update = self.cfg.version_update
                    show_in_garage = setting_relative["show_vehicle_in_garage"]
                    max_veh_front, max_veh_behind = max_relative_vehicles(
                        setting_relative["additional_players_front"],
                        setting_relative["additional_players_behind"])
                    is_split_mode = setting_standings["enable_multi_class_split_mode"]
                    min_top_veh = min_top_vehicles_in_class(
                        setting_standings["min_top_vehicles"])
                    veh_limit_all, veh_limit_other, veh_limit_player = max_vehicle_limit_set(
                        min_top_veh,
                        setting_standings["max_vehicles_combined_mode"],
                        setting_standings["max_vehicles_per_split_others"],
                        setting_standings["max_vehicles_per_split_player"])

                # Base info
                veh_total = max(api.read.vehicle.total_vehicles(), 1)
                plr_index = api.read.vehicle.player_index()
                plr_place = api.read.vehicle.place()

                # Get vehicles info
                (relative_ahead, relative_behind, classes_list, is_multi_class,
                 ) = get_vehicles_info(veh_total, plr_index, show_in_garage)

                # Create relative index list
                relative_index_list = create_relative_index(
                    relative_ahead, relative_behind, plr_index, max_veh_front, max_veh_behind)

                # Create vehicle class position list (initially ordered by class name)
                class_pos_list, plr_class_name, plr_class_place = create_position_in_class(
                    classes_list, plr_index)

                # Create standings index list
                if is_split_mode and is_multi_class:
                    standings_index_list = list(chain(*list(create_class_standings_index(
                        min_top_veh, class_pos_list, plr_class_name, plr_class_place,
                        veh_limit_other, veh_limit_player))))
                else:
                    classes_list.sort(key=itemgetter(1))  # sort by overall position
                    standings_index_list = calc_standings_index(
                        min_top_veh, veh_limit_all, plr_place, classes_list, 2)

                # Sort vehicle class position list (by player index) for output
                class_pos_list.sort()

                # Race/start grid, update only if vehicle number changed
                if last_veh_total != veh_total:
                    last_veh_total = veh_total
                    qualifications = create_qualify_position(veh_total)
                    output.qualifications = qualifications

                # Output data
                output.relative = relative_index_list
                output.standings = standings_index_list
                output.classes = class_pos_list

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval


def create_qualify_position(veh_total: int) -> list[tuple[int, int]]:
    """Create qualify position list

    Returns:
        list[(qualify overall, qualify in class)], ordered by "player index".
    """
    temp_class = sorted((
        api.read.vehicle.class_name(index),  # 0 class name
        api.read.vehicle.qualification(index),  # 1 qualification position
        index,  # 2 player index
    ) for index in range(veh_total))
    # Create grid position
    grid_classes = [QUALIFY_DEFAULT] * veh_total
    qualify_in_class = 0
    last_class_name = None
    for veh_data in temp_class:
        if last_class_name != veh_data[0]:
            last_class_name = veh_data[0]
            qualify_in_class = 1
        else:
            qualify_in_class += 1
        grid_classes[veh_data[2]] = (veh_data[1], qualify_in_class)
    return grid_classes


def get_vehicles_info(veh_total: int, plr_index: int, show_in_garage: bool):
    """Get vehicles info: relative time gap, classes, places, laptime"""
    laptime_est = api.read.timing.estimated_laptime()
    plr_time = api.read.timing.estimated_time_into()
    last_class_name = None
    classes_count = 0
    index_time = 0

    for index in range(veh_total):
        in_pit = api.read.vehicle.in_pits(index)
        in_garage = api.read.vehicle.in_garage(index)

        # Update relative time gap list
        if index != plr_index and laptime_est and (show_in_garage or not in_garage):
            opt_time = api.read.timing.estimated_time_into(index)
            diff_time = opt_time - plr_time
            diff_time_ahead = diff_time_behind = diff_time - diff_time // laptime_est * laptime_est
            if diff_time_ahead < 0:
                diff_time_ahead += laptime_est
            if diff_time_behind > 0:
                diff_time_behind -= laptime_est

            TEMP_RELATIVE_AHEAD[index_time][:] = (
                diff_time_ahead,  # 0 relative time gap
                index,  # 1 player index
            )
            TEMP_RELATIVE_BEHIND[index_time][:] = (
                diff_time_behind,  # 0 relative time gap
                index,  # 1 player index
            )
            index_time += 1

        # Update classes list
        class_name = api.read.vehicle.class_name(index)
        place_overall = api.read.vehicle.place(index)
        laptime_best = api.read.timing.best_laptime(index)
        laptime_last = api.read.timing.last_laptime(index)

        if laptime_last > 0 and not in_pit + in_garage:
            laptime_personal_last = laptime_last
        else:
            laptime_personal_last = MAX_SECONDS

        if laptime_best > 0:
            laptime_personal_best = laptime_best
        else:
            laptime_personal_best = MAX_SECONDS

        TEMP_CLASSES[index][:] = (
            class_name,  # 0 vehicle class name
            place_overall,  # 1 overall position/place
            index,  # 2 player index
            laptime_personal_best,  # 3 best lap time
            laptime_personal_last,  # 4 last lap time (for fastest last lap check)
        )

        # Check is multi classes
        if classes_count < 2 and last_class_name != class_name:
            last_class_name = class_name
            classes_count += 1

    # Sort output in-place
    relative_ahead = TEMP_RELATIVE_AHEAD[:index_time]
    relative_ahead.sort(reverse=True)  # by reversed time gap

    relative_behind = TEMP_RELATIVE_BEHIND[:index_time]
    relative_behind.sort(reverse=True)  # by reversed time gap

    new_classes = TEMP_CLASSES[:veh_total]
    new_classes.sort()  # by vehicle class

    return (
        relative_ahead,
        relative_behind,
        new_classes,  # -> classes_list
        classes_count > 1,  # -> is_multi_class
    )


def create_relative_index(
    relative_ahead: list, relative_behind: list, plr_index: int, max_veh_ahead: int, max_veh_behind: int):
    """Create player-centered relative (time, index) list"""
    ahead_cut = relative_ahead[max(len(relative_ahead) - max_veh_ahead, 0):]
    ahead_diff = max_veh_ahead - len(ahead_cut)
    if ahead_diff > 0:
        ahead_cut = [REL_TIME_DEFAULT] * ahead_diff + ahead_cut
    behind_cut = relative_behind[:min(len(relative_behind), max_veh_behind)]
    behind_diff = max_veh_behind - len(behind_cut)
    if behind_diff > 0:
        behind_cut += [REL_TIME_DEFAULT] * behind_diff
    return ahead_cut + [(0, plr_index)] + behind_cut


def create_position_in_class(sorted_veh_class: list, plr_index: int):
    """Create vehicle position in class list"""
    last_class_name = None
    place_in_class = 0
    opt_index_ahead = -1
    laptime_class_best = MAX_SECONDS
    last_fastest_laptime = MAX_SECONDS
    last_fastest_index = -1
    veh_total = len(sorted_veh_class)
    plr_class_name = ""
    plr_class_place = 0

    for index, veh_sort in enumerate(sorted_veh_class):
        opt_index = veh_sort[2]

        if last_class_name == veh_sort[0]:
            place_in_class += 1
            TEMP_CLASSES_POS[index - 1][5] = opt_index  # set opponent index behind
        else:
            last_class_name = veh_sort[0]  # reset class name
            place_in_class = 1  # reset position counter
            opt_index_ahead = -1  # no opponent ahead of class leader
            laptime_class_best = veh_sort[3]
            last_fastest_laptime = MAX_SECONDS  # reset last fastest
            if last_fastest_index != -1:  # mark fastest last lap
                TEMP_CLASSES_POS[last_fastest_index][6] = True
                last_fastest_index = -1  # reset last fastest index

        if opt_index == plr_index:
            plr_class_name = veh_sort[0]
            plr_class_place = place_in_class

        if last_fastest_laptime > veh_sort[4]:
            last_fastest_laptime = veh_sort[4]
            last_fastest_index = index

        TEMP_CLASSES_POS[index][:] = (
            opt_index,  # 0 - 2 player index
            place_in_class,  # 1 - position in class
            veh_sort[0],  # 2 - 0 class name
            laptime_class_best,  # 3 classes best
            opt_index_ahead,  # 4 opponent index ahead
            -1,  # 5 opponent index behind
            False,  # 6 is class fastest last laptime
        )
        opt_index_ahead = opt_index  # store opponent index for next

    if last_fastest_index != -1:  # mark for last class
        TEMP_CLASSES_POS[last_fastest_index][6] = True

    return TEMP_CLASSES_POS[:veh_total], plr_class_name, plr_class_place


def create_class_standings_index(
    min_top_veh: int, class_pos_list: list, plr_class_name: str, plr_class_place: int,
    veh_limit_other: int, veh_limit_player: int):
    """Generate class standings index list from class list collection"""
    class_collection = sorted(split_class_list(class_pos_list), key=sort_class_collection)
    for class_list in class_collection:
        if plr_class_name == class_list[0][2]:  # match class name
            veh_limit = veh_limit_player
            plr_place = plr_class_place  # 1 position in class
        else:
            veh_limit = veh_limit_other
            plr_place = 0
        yield calc_standings_index(min_top_veh, veh_limit, plr_place, class_list, 0)


def calc_standings_index(
    min_top_veh: int, veh_limit: int, plr_place: int, class_index_list: list, column: int):
    """Calculate vehicle standings index list"""
    veh_total = len(class_index_list)
    ref_place_list = create_reference_place(min_top_veh, veh_total, plr_place, veh_limit)
    # Create final standing index list
    return list(standings_index_from_place_reference(ref_place_list, class_index_list, veh_total, column))


def create_reference_place(
    min_top_veh: int, veh_total: int, plr_place: int, veh_limit: int):
    """Create reference place list"""
    if veh_total <= veh_limit:
        return REF_PLACES[:veh_total]
    if plr_place <= min_top_veh:
        return REF_PLACES[:veh_limit]
    # Find nearby slice range relative to player
    max_cut_range = veh_limit - min_top_veh
    # Number of rear slots, should be equal or less than front slots (exclude player slot)
    rear_cut_count = (max_cut_range - 1) // 2  # exclude player slot, then floor divide
    front_cut_count = max_cut_range - rear_cut_count  # include player slot
    # Find front slice limit
    front_cut_raw = plr_place - front_cut_count
    if front_cut_raw < min_top_veh:
        front_cut_raw = min_top_veh
    # Find rear slice limit
    rear_cut_max = front_cut_raw + max_cut_range
    if rear_cut_max > veh_total:
        rear_cut_max = veh_total
    front_cut_max = rear_cut_max - max_cut_range
    return REF_PLACES[:min_top_veh] + REF_PLACES[front_cut_max:rear_cut_max]


def standings_index_from_place_reference(
    ref_place_list: tuple, class_index_list: list, veh_total: int, column: int):
    """Match place from reference list to generate standings player index list"""
    for ref_idx in ref_place_list:
        if 0 < ref_idx <= veh_total:  # prevent out of range
            yield class_index_list[ref_idx - 1][column]  # column - player index
        else:
            break
    yield -1  # append an empty index as gap between classes


def split_class_list(class_list: list):
    """Split class list into class collection"""
    class_name = class_list[0][2]
    index_start = 0
    index_end = 0
    for vehicle in class_list:
        if vehicle[2] == class_name:
            index_end +=1
        elif vehicle[2] != class_name:
            class_name = vehicle[2]
            yield class_list[index_start:index_end]
            index_start = index_end
            index_end +=1
    # Final split
    yield class_list[index_start:index_end]


def max_relative_vehicles(add_front: int, add_behind: int):
    """Maximum number of vehicles in relative list"""
    add_front = int(zero_max(add_front, 60)) + 3
    add_behind = int(zero_max(add_behind, 60)) + 3
    return add_front, add_behind


def min_top_vehicles_in_class(min_top_veh: int) -> int:
    """Minimum number of top vehicles in class list

    min_top_veh: value range limited in 1 to 5
    """
    return int(asym_max(min_top_veh, 1, 5))


def max_vehicles_in_class(max_cls_veh: int, min_top_veh: int, min_add_veh: int = 0) -> int:
    """Maximum number of vehicles in class list

    max_cls_veh: maximum vehicles per class limit
    min_top_veh: minimum top vehicles limit
    min_add_veh: minimum addition vehicles limit (for class has local player)
    """
    return max(int(max_cls_veh), min_top_veh + min_add_veh)


def max_vehicle_limit_set(
    min_top_veh: int, max_all: int, max_others: int, max_player: int):
    """Create max vehicle limit set"""
    limit_all = max_vehicles_in_class(max_all, min_top_veh, 2)
    limit_other = max_vehicles_in_class(max_others, min_top_veh)
    limit_player = max_vehicles_in_class(max_player, min_top_veh, 2)
    return limit_all, limit_other, limit_player


def sort_class_collection(collection: list) -> float:
    """Sort class collection by class best laptime"""
    return collection[0][3]  # 3 class best laptime
