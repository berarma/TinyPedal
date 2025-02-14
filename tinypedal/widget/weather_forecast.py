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
Weather forecast Widget
"""

from __future__ import annotations

from PySide2.QtCore import Qt, QRect
from PySide2.QtGui import QPixmap, QPainter

from .. import calculation as calc
from .. import weather as wthr
from ..regex_pattern import TEXT_NOTAVAILABLE
from ..api_control import api
from ..module_info import minfo, WeatherNode
from ._base import Overlay

MAX_FORECASTS = 5


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout(gap_hori=self.wcfg["bar_gap"])
        self.set_primary_layout(layout=layout)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        layout_reversed = self.wcfg["layout"] != 0
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        icon_size = int(max(self.wcfg["icon_size"], 16) * 0.5) * 2
        self.total_slot = min(max(self.wcfg["number_of_forecasts"], 1), MAX_FORECASTS - 1) + 1
        self.bar_width = max(font_m.width * 4 + bar_padx, icon_size)
        self.bar_rain_height = max(self.wcfg["rain_chance_bar_height"], 1)

        # Base style
        self.setStyleSheet(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # Config canvas
        self.pixmap_weather = create_weather_icon_set(icon_size)
        self.pixmap_rainchance = QPixmap(self.bar_width, self.bar_rain_height)

        # Estimated time
        if self.wcfg["show_estimated_time"]:
            bar_style_time = self.set_qss(
                fg_color=self.wcfg["font_color_estimated_time"],
                bg_color=self.wcfg["bkg_color_estimated_time"]
            )
            self.bars_time = self.set_qlabel(
                text=TEXT_NOTAVAILABLE,
                style=bar_style_time,
                fixed_width=self.bar_width,
                count=self.total_slot,
            )
            self.bars_time[0].setText("now")
            self.set_grid_layout_table_row(
                layout=layout,
                targets=self.bars_time,
                row_index=self.wcfg["column_index_estimated_time"],
                right_to_left=layout_reversed,
            )

        # Ambient temperature
        if self.wcfg["show_ambient_temperature"]:
            bar_style_temp = self.set_qss(
                fg_color=self.wcfg["font_color_ambient_temperature"],
                bg_color=self.wcfg["bkg_color_ambient_temperature"]
            )
            self.bars_temp = self.set_qlabel(
                text=TEXT_NOTAVAILABLE,
                style=bar_style_temp,
                fixed_width=self.bar_width,
                count=self.total_slot,
            )
            self.set_grid_layout_table_row(
                layout=layout,
                targets=self.bars_temp,
                row_index=self.wcfg["column_index_ambient_temperature"],
                right_to_left=layout_reversed,
            )

        # Rain chance
        if self.wcfg["show_rain_chance_bar"]:
            bar_style_rain = self.set_qss(
                bg_color=self.wcfg["rain_chance_bar_bkg_color"]
            )
            self.bars_rain = self.set_qlabel(
                style=bar_style_rain,
                fixed_width=self.bar_width,
                fixed_height=self.bar_rain_height,
                count=self.total_slot,
            )
            self.set_grid_layout_table_row(
                layout=layout,
                targets=self.bars_rain,
                row_index=self.wcfg["column_index_rain_chance_bar"],
                right_to_left=layout_reversed,
            )

        # Forecast icon
        bar_style_icon = self.set_qss(
            bg_color=self.wcfg["bkg_color"]
        )
        self.bars_icon = self.set_qlabel(
            pixmap=self.pixmap_weather[-1],
            style=bar_style_icon,
            fixed_width=self.bar_width,
            count=self.total_slot,
        )
        self.set_grid_layout_table_row(
            layout=layout,
            targets=self.bars_icon,
            row_index=self.wcfg["column_index_weather_icon"],
            right_to_left=layout_reversed,
        )

        # Last data
        self.estimated_time = [wthr.MAX_MINUTES] * MAX_FORECASTS

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if self.state.active:
            self.update_weather_forecast_restapi()

    def update_weather_forecast_restapi(self):
        """Update weather forecast from restapi"""
        # Read weather data
        is_lap_type = api.read.session.lap_type()
        forecast_info = get_forecast_info(api.read.session.session_type())
        forecast_count = min(len(forecast_info), MAX_FORECASTS)

        if forecast_count < 1:
            return

        if is_lap_type:
            index_offset = 0
        else:  # time type race, add index offset to ignore negative estimated time
            index_offset = self.set_forecast_time(forecast_info)

        # Forecast
        for index in range(self.total_slot):
            index_bias = index + index_offset

            # Update slot 0 with live(now) weather condition
            if index == 0:
                rain_chance = api.read.session.raininess() * 100
                icon_index = wthr.sky_type_correction(forecast_info[index_bias].sky_type, rain_chance)
                estimated_temp = api.read.session.ambient_temperature()
                estimated_time = 0
            # Update slot with available forecast
            elif index_bias < forecast_count:
                rain_chance = forecast_info[index_bias].rain_chance
                icon_index = forecast_info[index_bias].sky_type
                estimated_temp = forecast_info[index_bias].temperature
                if is_lap_type:
                    estimated_time = wthr.MAX_MINUTES
                else:
                    estimated_time = self.estimated_time[index_bias]
            # Update slot with unavailable forecast
            else:
                rain_chance = 0
                icon_index = -1
                estimated_temp = wthr.MIN_TEMPERATURE
                estimated_time = wthr.MAX_MINUTES

            self.update_weather_icon(self.bars_icon[index], icon_index, index)

            if self.wcfg["show_estimated_time"] and index > 0:
                self.update_estimated_time(self.bars_time[index], estimated_time)

            if self.wcfg["show_ambient_temperature"]:
                self.update_estimated_temp(self.bars_temp[index], estimated_temp)

            if self.wcfg["show_rain_chance_bar"]:
                self.update_rain_chance_bar(self.bars_rain[index], rain_chance)

    # GUI update methods
    def update_estimated_time(self, target, data):
        """Estimated time"""
        if target.last != data:
            target.last = data
            if data >= wthr.MAX_MINUTES or data < 0:
                time_text = TEXT_NOTAVAILABLE
            elif data >= 60:
                time_text = f"{data / 60:.1f}h"
            else:
                time_text = f"{data:.0f}m"
            target.setText(time_text)

    def update_estimated_temp(self, target, data):
        """Estimated temperature"""
        if target.last != data:
            target.last = data
            if data > wthr.MIN_TEMPERATURE:
                temp_text = self.format_temperature(data)
            else:
                temp_text = TEXT_NOTAVAILABLE
            target.setText(temp_text)

    def update_rain_chance_bar(self, target, data):
        """Rain chance bar"""
        if target.last != data:
            target.last = data
            self.pixmap_rainchance.fill(Qt.transparent)
            painter = QPainter(self.pixmap_rainchance)
            painter.fillRect(
                0, 0, data * 0.01 * self.bar_width, self.bar_rain_height,
                self.wcfg["rain_chance_bar_color"]
            )
            target.setPixmap(self.pixmap_rainchance)

    def update_weather_icon(self, target, icon_index, slot_index):
        """Weather icon, toggle visibility"""
        if target.last != icon_index:
            target.last = icon_index
            if not 0 <= icon_index <= 10:
                icon_index = -1
            target.setPixmap(self.pixmap_weather[icon_index])

            if not self.wcfg["show_unavailable_data"] and slot_index > 0:  # skip first slot
                unavailable = icon_index < 0
                self.bars_icon[slot_index].setHidden(unavailable)
                if self.wcfg["show_estimated_time"]:
                    self.bars_time[slot_index].setHidden(unavailable)
                if self.wcfg["show_ambient_temperature"]:
                    self.bars_temp[slot_index].setHidden(unavailable)
                if self.wcfg["show_rain_chance_bar"]:
                    self.bars_rain[slot_index].setHidden(unavailable)

    # Additional methods
    def format_temperature(self, air_deg):
        """Format ambient temperature"""
        if self.cfg.units["temperature_unit"] == "Fahrenheit":
            return f"{calc.celsius2fahrenheit(air_deg):.0f}°"
        return f"{air_deg:.0f}°"

    def set_forecast_time(self, forecast_info: list[WeatherNode]) -> int:
        """Set forecast estimated time"""
        index_offset = 0
        session_length = api.read.session.end()
        elapsed_time = api.read.session.elapsed()
        for index, forecast in enumerate(forecast_info):
            if index == 0:
                continue
            _time = self.estimated_time[index] = min(round(
                wthr.forecast_time_progress(
                    forecast.start_minute, session_length, elapsed_time,
                ) / 60), wthr.MAX_MINUTES)
            if _time <= 0:
                index_offset += 1
        return index_offset


def get_forecast_info(session_type: int) -> list[WeatherNode]:
    """Get forecast info"""
    if session_type <= 1:  # practice session
        info = minfo.restapi.forecastPractice
    elif session_type == 2:  # qualify session
        info = minfo.restapi.forecastQualify
    else:
        info = minfo.restapi.forecastRace  # race session
    if info:
        return info
    return wthr.DEFAULT  # get default if no valid data


def create_weather_icon_set(icon_size: int):
    """Create weather icon set"""
    icon_source = QPixmap("images/icon_weather.png")
    pixmap_icon = icon_source.scaledToWidth(icon_size * 12, mode=Qt.SmoothTransformation)
    rect_size = QRect(0, 0, icon_size, icon_size)
    rect_offset = QRect(0, 0, icon_size, icon_size)
    return tuple(
        draw_weather_icon(pixmap_icon, icon_size, rect_size, rect_offset, index)
        for index in range(12))


def draw_weather_icon(
    pixmap_icon: QPixmap, icon_size: int, rect_size: QRect, rect_offset: QRect, h_offset: int):
    """Draw weather icon"""
    pixmap = QPixmap(icon_size, icon_size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    rect_offset.moveLeft(icon_size * h_offset)
    painter.drawPixmap(rect_size, pixmap_icon, rect_offset)
    return pixmap
