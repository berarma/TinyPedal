#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2024 TinyPedal developers, see contributors.md file
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
Stats module
"""

from __future__ import annotations

from ._base import DataModule
from ..module_info import minfo
from ..api_control import api
from .. import calculation as calc
from ..userfile.driver_stats import load_driver_stats, save_driver_stats


class Realtime(DataModule):
    """Delta time data"""

    def __init__(self, config, module_name):
        super().__init__(config, module_name)

    def update_data(self):
        """Update module data"""
        reset = False
        update_interval = self.active_interval

        output = minfo.stats
        max_moved_distance = 1500 * update_interval
        podium_by_class = self.mcfg["enable_podium_by_class"]
        vehicle_class = self.mcfg["vehicle_classification"]

        while not self._event.wait(update_interval):

            # Ignore stats while in override mode
            if (self.cfg.shared_memory_api["enable_player_index_override"]
                or self.cfg.shared_memory_api["enable_active_state_override"]):
                reset = False  # make sure stats not saved
                update_interval = self.idle_interval
                continue

            if self.state.active:
                if not reset:

                    reset = True
                    update_interval = self.active_interval

                    is_pit_lap = 0
                    last_lap_stime = float("inf")
                    last_lap_etime = float("inf")
                    last_best_laptime = float("inf")
                    last_num_penalties = 99999
                    fuel_last = 0.0
                    last_finish_state = 99999
                    gps_last = (-99999, -99999, -99999)
                    driver_stats = load_driver_stats(
                        key_list=self.stats_keys(vehicle_class),
                        filepath=self.cfg.path.config,
                    )

                # General
                lap_stime = api.read.timing.start()
                lap_etime = api.read.timing.elapsed()
                is_pit_lap |= api.read.vehicle.in_pits()

                # Best lap time
                best_laptime = api.read.timing.best_laptime()
                if last_best_laptime > best_laptime > 1:
                    last_best_laptime = best_laptime
                    if driver_stats.pb > best_laptime:
                        driver_stats.pb = best_laptime

                # Driven distance
                gps_curr = api.read.vehicle.position_xyz()
                if gps_last != gps_curr:
                    moved_distance = calc.distance(gps_last, gps_curr)
                    if moved_distance < max_moved_distance:
                        driver_stats.meters += moved_distance
                    gps_last = gps_curr

                # Laps complete
                if last_lap_stime > lap_stime:
                    last_lap_stime = lap_stime
                elif last_lap_stime < lap_stime and lap_etime - lap_stime > 2:
                    if api.read.timing.last_laptime() > 0: # valid lap check
                        driver_stats.valid += 1  # 1 lap at a time
                    elif not is_pit_lap:  # only count non-pit invalid lap
                        driver_stats.invalid += 1
                    is_pit_lap = 0
                    last_lap_stime = lap_stime

                # Seconds spent
                if last_lap_etime > lap_etime:
                    last_lap_etime = lap_etime
                elif last_lap_etime < lap_etime:
                    if api.read.vehicle.speed() > 1:  # while speed > 1m/s
                        driver_stats.seconds += lap_etime - last_lap_etime
                    last_lap_etime = lap_etime

                # Fuel consumed (liter)
                fuel_curr = api.read.vehicle.fuel()
                if fuel_last < fuel_curr:
                    fuel_last = fuel_curr
                elif fuel_last > fuel_curr:
                    driver_stats.liters += fuel_last - fuel_curr
                    fuel_last = fuel_curr

                # Race-only stats
                if api.read.session.in_race():
                    # Penalties
                    num_penalties = api.read.vehicle.number_penalties()
                    if last_num_penalties > num_penalties:
                        last_num_penalties = num_penalties
                    elif last_num_penalties < num_penalties:
                        driver_stats.penalties += num_penalties - last_num_penalties
                        last_num_penalties = num_penalties

                    # Finish place
                    finish_state = api.read.vehicle.finish_state()
                    if last_finish_state > finish_state:
                        last_finish_state = finish_state
                    elif 0 == last_finish_state < finish_state:
                        last_finish_state = finish_state
                        if finish_state == 1:  # finished
                            driver_stats.races += 1
                            finish_place = finish_position(podium_by_class)
                            if finish_place == 1:
                                driver_stats.wins += 1
                            if finish_place <= 3:
                                driver_stats.podiums += 1

                # Output stats data
                output.metersDriven = driver_stats.meters

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval
                    save_driver_stats(
                        key_list=self.stats_keys(vehicle_class),
                        stats_update=driver_stats,
                        filepath=self.cfg.path.config,
                    )

    def stats_keys(self, vehicle_class: str) -> tuple[str, ...]:
        """Stats key names"""
        if vehicle_class == "Class":
            name = api.read.vehicle.class_name()
        elif vehicle_class == "Class - Brand":
            brand_name = self.cfg.user.brands.get(api.read.vehicle.vehicle_name(), "")
            class_name = api.read.vehicle.class_name()
            if brand_name:
                name = f"{class_name} - {brand_name}"
            else:  # fallback to class name
                name = class_name
        else:
            name = api.read.vehicle.vehicle_name()
        return api.read.session.track_name(), name


def finish_position(podium_by_class: bool) -> int:
    """Get finish position"""
    # Overall position
    plr_place = api.read.vehicle.place()
    if not podium_by_class:
        return plr_place
    # Position in class
    veh_total = api.read.vehicle.total_vehicles()
    plr_class = api.read.vehicle.class_name()
    total_class_vehicle = 0
    place_higher = 0
    for index in range(veh_total):
        if api.read.vehicle.class_name(index) == plr_class:
            total_class_vehicle += 1
            if api.read.vehicle.place(index) > plr_place:
                place_higher += 1
    return total_class_vehicle - place_higher
