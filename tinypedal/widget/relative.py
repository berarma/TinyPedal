#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022  Xiang
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
Relative Widget
"""

import tkinter as tk
import tkinter.font as tkfont

from .. import readapi as read_data
from ..base import Widget, MouseEvent
from ..module_control import module
from ..setting import VehicleClass

WIDGET_NAME = "relative"


class Draw(Widget, MouseEvent):
    """Draw widget"""

    def __init__(self, config):
        # Assign base setting
        Widget.__init__(self, config, WIDGET_NAME)

        # Config size & position
        self.geometry(f"+{self.wcfg['position_x']}+{self.wcfg['position_y']}")

        bar_padx = self.wcfg["font_size"] * 0.3
        bar_gap = self.wcfg["bar_gap"]
        num_width = 3
        gap_width = self.wcfg["bar_time_gap_width"]
        self.drv_width = self.wcfg["bar_driver_name_width"]
        self.cls_width = self.wcfg["bar_class_name_width"]

        # Config style & variable
        text_def = ""
        fg_color = "#FFF"  # placeholder, font color for place, name, gap changes dynamically
        fg_color_plr = self.wcfg["font_color_player"]
        bg_color_place = self.wcfg["bkg_color_place"]
        bg_color_place_plr = self.wcfg["bkg_color_player_place"]
        bg_color_name = self.wcfg["bkg_color_name"]
        bg_color_name_plr = self.wcfg["bkg_color_player_name"]
        bg_color_gap = self.wcfg["bkg_color_gap"]
        bg_color_gap_plr = self.wcfg["bkg_color_player_gap"]

        column_plc = self.wcfg["column_index_place"]
        column_drv = self.wcfg["column_index_driver"]
        column_lpt = self.wcfg["column_index_laptime"]
        column_pic = self.wcfg["column_index_position_in_class"]
        column_cls = self.wcfg["column_index_class"]
        column_tcp = self.wcfg["column_index_tyre_compound"]
        column_gap = self.wcfg["column_index_time_gap"]
        column_pit = self.wcfg["column_index_pit_status"]

        font_relative = tkfont.Font(family=self.wcfg["font_name"],
                                    size=-self.wcfg["font_size"],
                                    weight=self.wcfg["font_weight"])
        plr_row = 9  # set player row number

        # Max display players
        self.rel_add_front = min(max(self.wcfg["additional_players_front"], 0), 3)
        self.rel_add_behind = min(max(self.wcfg["additional_players_behind"], 0), 3)

        # Draw label
        # Driver place number
        bar_style_plc = {"text":text_def, "bd":0, "padx":0, "pady":0, "font":font_relative,
                         "height":1, "width":num_width, "fg":fg_color, "bg":bg_color_place}

        self.row_plr_plc = tk.Label(self, text=text_def, bd=0, padx=0, pady=0,
                                    font=font_relative, height=1, width=num_width,
                                    fg=fg_color_plr, bg=bg_color_place_plr)
        self.row_plr_plc.grid(row=plr_row, column=column_plc, padx=0, pady=(0, bar_gap))

        self.generate_bar("plc", bar_style_plc, plr_row, column_plc, bar_gap)

        # Driver name
        bar_style_drv = {"text":text_def, "bd":0, "padx":bar_padx, "pady":0,
                         "font":font_relative, "height":1, "width":self.drv_width,
                         "fg":fg_color, "bg":bg_color_name, "anchor":"w"}

        self.row_plr_drv = tk.Label(self, text=text_def, bd=0, padx=bar_padx, pady=0,
                                    font=font_relative, height=1, width=self.drv_width,
                                    fg=fg_color_plr, bg=bg_color_name_plr, anchor="w")
        self.row_plr_drv.grid(row=plr_row, column=column_drv, padx=0, pady=(0, bar_gap))

        self.generate_bar("drv", bar_style_drv, plr_row, column_drv, bar_gap)

        # Time gap
        bar_style_gap = {"text":text_def, "bd":0, "padx":bar_padx, "pady":0,
                         "font":font_relative, "height":1, "width":gap_width,
                         "fg":fg_color, "bg":bg_color_gap, "anchor":"e"}

        self.row_plr_gap = tk.Label(self, text=text_def, bd=0, padx=bar_padx, pady=0,
                                    font=font_relative, height=1, width=gap_width,
                                    fg=fg_color_plr, bg=bg_color_gap_plr, anchor="e")
        self.row_plr_gap.grid(row=plr_row, column=column_gap, padx=0, pady=(0, bar_gap))

        self.generate_bar("gap", bar_style_gap, plr_row, column_gap, bar_gap)

        # Vehicle laptime
        if self.wcfg["show_laptime"]:
            bar_style_lpt = {"text":text_def, "bd":0, "padx":bar_padx, "pady":0,
                             "font":font_relative, "height":1, "width":9,
                             "fg":self.wcfg['font_color_laptime'],
                             "bg":self.wcfg['bkg_color_laptime']}

            self.row_plr_lpt = tk.Label(self, text=text_def, bd=0, padx=bar_padx, pady=0,
                                        font=font_relative, height=1, width=9,
                                        fg=fg_color_plr, bg=bg_color_name_plr)
            self.row_plr_lpt.grid(row=plr_row, column=column_lpt, padx=0, pady=(0, bar_gap))

            self.generate_bar("lpt", bar_style_lpt, plr_row, column_lpt, bar_gap)

        # Vehicle position in class
        if self.wcfg["show_position_in_class"]:
            bar_style_pic = {"text":text_def, "bd":0, "padx":0, "pady":0, "font":font_relative,
                             "height":1, "width":num_width,
                             "fg":self.wcfg['font_color_position_in_class'],
                             "bg":self.wcfg['bkg_color_position_in_class']}

            self.row_plr_pic = tk.Label(self, bar_style_pic)
            self.row_plr_pic.grid(row=plr_row, column=column_pic, padx=0, pady=(0, bar_gap))

            self.generate_bar("pic", bar_style_pic, plr_row, column_pic, bar_gap)

        # Vehicle class
        if self.wcfg["show_class"]:
            self.vehcls = VehicleClass()  # load VehicleClass config
            bar_style_cls = {"text":text_def, "bd":0, "padx":bar_padx, "pady":0, "font":font_relative,
                             "height":1, "width":self.cls_width,
                             "fg":self.wcfg['font_color_class'],
                             "bg":self.wcfg['bkg_color_class']}

            self.row_plr_cls = tk.Label(self, bar_style_cls)
            self.row_plr_cls.grid(row=plr_row, column=column_cls, padx=0, pady=(0, bar_gap))

            self.generate_bar("cls", bar_style_cls, plr_row, column_cls, bar_gap)

        # Vehicle in pit
        if self.wcfg["show_pit_status"]:
            bar_style_pit = {"text":text_def, "bd":0, "padx":0, "pady":0, "font":font_relative,
                             "height":1, "width":len(self.wcfg["pit_status_text"])+1,
                             "fg":self.wcfg['font_color_pit'],
                             "bg":self.wcfg['bkg_color_pit']}

            self.row_plr_pit = tk.Label(self, bar_style_pit)
            self.row_plr_pit.grid(row=plr_row, column=column_pit, padx=0, pady=(0, bar_gap))

            self.generate_bar("pit", bar_style_pit, plr_row, column_pit, bar_gap)

        # Tyre compound index
        if self.wcfg["show_tyre_compound"]:
            bar_style_tcp = {"text":text_def, "bd":0, "padx":bar_padx, "pady":0, "font":font_relative,
                             "height":1, "width":2,
                             "fg":self.wcfg['font_color_tyre_compound'],
                             "bg":self.wcfg['bkg_color_tyre_compound']}

            self.row_plr_tcp = tk.Label(self, bar_style_tcp)
            self.row_plr_tcp.grid(row=plr_row, column=column_tcp, padx=0, pady=(0, bar_gap))

            self.generate_bar("tcp", bar_style_tcp, plr_row, column_tcp, bar_gap)

        self.update_data()

        # Assign mouse event
        MouseEvent.__init__(self)

    def generate_bar(self, suffix, style, row_idx, column_idx, bar_gap):
        """Generate data bar"""
        for idx in range(1,4):
            setattr(self, f"row_f_{idx:02.0f}_{suffix}", tk.Label(self, style))  # front row
            getattr(self, f"row_f_{idx:02.0f}_{suffix}").grid(
                row=row_idx - idx, column=column_idx, padx=0, pady=(0, bar_gap))

            setattr(self, f"row_r_{idx:02.0f}_{suffix}", tk.Label(self, style))  # rear row
            getattr(self, f"row_r_{idx:02.0f}_{suffix}").grid(
                row=row_idx + idx, column=column_idx, padx=0, pady=(0, bar_gap))

            if self.rel_add_front > (idx - 1):
                setattr(self, f"row_f_{idx+3:02.0f}_{suffix}", tk.Label(self, style))  # additional front row
                getattr(self, f"row_f_{idx+3:02.0f}_{suffix}").grid(
                    row=row_idx - idx - 3, column=column_idx, padx=0, pady=(0, bar_gap))

            if self.rel_add_behind > (idx - 1):
                setattr(self, f"row_r_{idx+3:02.0f}_{suffix}", tk.Label(self, style))  # additional rear row
                getattr(self, f"row_r_{idx+3:02.0f}_{suffix}").grid(
                    row=row_idx + idx + 3, column=column_idx, padx=0, pady=(0, bar_gap))

    def update_data(self):
        """Update when vehicle on track"""
        if read_data.state() and module.relative_info.relative_list and self.wcfg["enable"]:

            # Read relative data
            rel_idx, cls_info, plr_idx = module.relative_info.relative_list
            veh_center = int(3 + self.rel_add_front)

            # Start updating
            # 0 place, 1 driver, 2 laptime, 3 pos_class, 4 veh_f_01lass, 5 time_gap, 6 num_lap, 7 in_pit
            veh_plr = module.relative_info.relative_data(plr_idx, plr_idx, cls_info)

            veh_f_03 = module.relative_info.relative_data(rel_idx[veh_center - 3], plr_idx, cls_info)
            veh_f_02 = module.relative_info.relative_data(rel_idx[veh_center - 2], plr_idx, cls_info)
            veh_f_01 = module.relative_info.relative_data(rel_idx[veh_center - 1], plr_idx, cls_info)
            veh_r_01 = module.relative_info.relative_data(rel_idx[veh_center + 1], plr_idx, cls_info)
            veh_r_02 = module.relative_info.relative_data(rel_idx[veh_center + 2], plr_idx, cls_info)
            veh_r_03 = module.relative_info.relative_data(rel_idx[veh_center + 3], plr_idx, cls_info)

            if self.rel_add_front > 0:
                veh_f_04 = module.relative_info.relative_data(rel_idx[veh_center - 4], plr_idx, cls_info)
            if self.rel_add_behind > 0:
                veh_r_04 = module.relative_info.relative_data(rel_idx[veh_center + 4], plr_idx, cls_info)
            if self.rel_add_front > 1:
                veh_f_05 = module.relative_info.relative_data(rel_idx[veh_center - 5], plr_idx, cls_info)
            if self.rel_add_behind > 1:
                veh_r_05 = module.relative_info.relative_data(rel_idx[veh_center + 5], plr_idx, cls_info)
            if self.rel_add_front > 2:
                veh_f_06 = module.relative_info.relative_data(rel_idx[veh_center - 6], plr_idx, cls_info)
            if self.rel_add_behind > 2:
                veh_r_06 = module.relative_info.relative_data(rel_idx[veh_center + 6], plr_idx, cls_info)

            # Relative update
            # Driver place
            self.row_plr_plc.config(text=veh_plr[0])

            self.row_f_03_plc.config(text=veh_f_03[0], fg=self.color_lapdiff(veh_f_03[6], veh_plr[6]))
            self.row_f_02_plc.config(text=veh_f_02[0], fg=self.color_lapdiff(veh_f_02[6], veh_plr[6]))
            self.row_f_01_plc.config(text=veh_f_01[0], fg=self.color_lapdiff(veh_f_01[6], veh_plr[6]))
            self.row_r_01_plc.config(text=veh_r_01[0], fg=self.color_lapdiff(veh_r_01[6], veh_plr[6]))
            self.row_r_02_plc.config(text=veh_r_02[0], fg=self.color_lapdiff(veh_r_02[6], veh_plr[6]))
            self.row_r_03_plc.config(text=veh_r_03[0], fg=self.color_lapdiff(veh_r_03[6], veh_plr[6]))

            if self.rel_add_front > 0:
                self.row_f_04_plc.config(text=veh_f_04[0], fg=self.color_lapdiff(veh_f_04[6], veh_plr[6]))
            if self.rel_add_behind > 0:
                self.row_r_04_plc.config(text=veh_r_04[0], fg=self.color_lapdiff(veh_r_04[6], veh_plr[6]))
            if self.rel_add_front > 1:
                self.row_f_05_plc.config(text=veh_f_05[0], fg=self.color_lapdiff(veh_f_05[6], veh_plr[6]))
            if self.rel_add_behind > 1:
                self.row_r_05_plc.config(text=veh_r_05[0], fg=self.color_lapdiff(veh_r_05[6], veh_plr[6]))
            if self.rel_add_front > 2:
                self.row_f_06_plc.config(text=veh_f_06[0], fg=self.color_lapdiff(veh_f_06[6], veh_plr[6]))
            if self.rel_add_behind > 2:
                self.row_r_06_plc.config(text=veh_r_06[0], fg=self.color_lapdiff(veh_r_06[6], veh_plr[6]))

            # Driver name
            self.row_plr_drv.config(text=veh_plr[1][:self.drv_width])

            self.row_f_03_drv.config(text=veh_f_03[1][:self.drv_width], fg=self.color_lapdiff(veh_f_03[6], veh_plr[6]))
            self.row_f_02_drv.config(text=veh_f_02[1][:self.drv_width], fg=self.color_lapdiff(veh_f_02[6], veh_plr[6]))
            self.row_f_01_drv.config(text=veh_f_01[1][:self.drv_width], fg=self.color_lapdiff(veh_f_01[6], veh_plr[6]))
            self.row_r_01_drv.config(text=veh_r_01[1][:self.drv_width], fg=self.color_lapdiff(veh_r_01[6], veh_plr[6]))
            self.row_r_02_drv.config(text=veh_r_02[1][:self.drv_width], fg=self.color_lapdiff(veh_r_02[6], veh_plr[6]))
            self.row_r_03_drv.config(text=veh_r_03[1][:self.drv_width], fg=self.color_lapdiff(veh_r_03[6], veh_plr[6]))

            if self.rel_add_front > 0:
                self.row_f_04_drv.config(text=veh_f_04[1][:self.drv_width], fg=self.color_lapdiff(veh_f_04[6], veh_plr[6]))
            if self.rel_add_behind > 0:
                self.row_r_04_drv.config(text=veh_r_04[1][:self.drv_width], fg=self.color_lapdiff(veh_r_04[6], veh_plr[6]))
            if self.rel_add_front > 1:
                self.row_f_05_drv.config(text=veh_f_05[1][:self.drv_width], fg=self.color_lapdiff(veh_f_05[6], veh_plr[6]))
            if self.rel_add_behind > 1:
                self.row_r_05_drv.config(text=veh_r_05[1][:self.drv_width], fg=self.color_lapdiff(veh_r_05[6], veh_plr[6]))
            if self.rel_add_front > 2:
                self.row_f_06_drv.config(text=veh_f_06[1][:self.drv_width], fg=self.color_lapdiff(veh_f_06[6], veh_plr[6]))
            if self.rel_add_behind > 2:
                self.row_r_06_drv.config(text=veh_r_06[1][:self.drv_width], fg=self.color_lapdiff(veh_r_06[6], veh_plr[6]))

            # Vehicle laptime
            if self.wcfg["show_laptime"]:
                self.row_plr_lpt.config(text=veh_plr[2])

                self.row_f_03_lpt.config(text=veh_f_03[2])
                self.row_f_02_lpt.config(text=veh_f_02[2])
                self.row_f_01_lpt.config(text=veh_f_01[2])
                self.row_r_01_lpt.config(text=veh_r_01[2])
                self.row_r_02_lpt.config(text=veh_r_02[2])
                self.row_r_03_lpt.config(text=veh_r_03[2])

                if self.rel_add_front > 0:
                    self.row_f_04_lpt.config(text=veh_f_04[2])
                if self.rel_add_behind > 0:
                    self.row_r_04_lpt.config(text=veh_r_04[2])
                if self.rel_add_front > 1:
                    self.row_f_05_lpt.config(text=veh_f_05[2])
                if self.rel_add_behind > 1:
                    self.row_r_05_lpt.config(text=veh_r_05[2])
                if self.rel_add_front > 2:
                    self.row_f_06_lpt.config(text=veh_f_06[2])
                if self.rel_add_behind > 2:
                    self.row_r_06_lpt.config(text=veh_r_06[2])

            # Vehicle position in class
            if self.wcfg["show_position_in_class"]:
                self.row_plr_pic.config(text=veh_plr[3])

                self.row_f_03_pic.config(text=veh_f_03[3])
                self.row_f_02_pic.config(text=veh_f_02[3])
                self.row_f_01_pic.config(text=veh_f_01[3])
                self.row_r_01_pic.config(text=veh_r_01[3])
                self.row_r_02_pic.config(text=veh_r_02[3])
                self.row_r_03_pic.config(text=veh_r_03[3])

                if self.rel_add_front > 0:
                    self.row_f_04_pic.config(text=veh_f_04[3])
                if self.rel_add_behind > 0:
                    self.row_r_04_pic.config(text=veh_r_04[3])
                if self.rel_add_front > 1:
                    self.row_f_05_pic.config(text=veh_f_05[3])
                if self.rel_add_behind > 1:
                    self.row_r_05_pic.config(text=veh_r_05[3])
                if self.rel_add_front > 2:
                    self.row_f_06_pic.config(text=veh_f_06[3])
                if self.rel_add_behind > 2:
                    self.row_r_06_pic.config(text=veh_r_06[3])

            # Vehicle class
            if self.wcfg["show_class"]:
                self.row_plr_cls.config(self.set_class_style(veh_plr[4]))

                self.row_f_03_cls.config(self.set_class_style(veh_f_03[4]))
                self.row_f_02_cls.config(self.set_class_style(veh_f_02[4]))
                self.row_f_01_cls.config(self.set_class_style(veh_f_01[4]))
                self.row_r_01_cls.config(self.set_class_style(veh_r_01[4]))
                self.row_r_02_cls.config(self.set_class_style(veh_r_02[4]))
                self.row_r_03_cls.config(self.set_class_style(veh_r_03[4]))

                if self.rel_add_front > 0:
                    self.row_f_04_cls.config(self.set_class_style(veh_f_04[4]))
                if self.rel_add_behind > 0:
                    self.row_r_04_cls.config(self.set_class_style(veh_r_04[4]))
                if self.rel_add_front > 1:
                    self.row_f_05_cls.config(self.set_class_style(veh_f_05[4]))
                if self.rel_add_behind > 1:
                    self.row_r_05_cls.config(self.set_class_style(veh_r_05[4]))
                if self.rel_add_front > 2:
                    self.row_f_06_cls.config(self.set_class_style(veh_f_06[4]))
                if self.rel_add_behind > 2:
                    self.row_r_06_cls.config(self.set_class_style(veh_r_06[4]))

            # Tyre compound index
            if self.wcfg["show_tyre_compound"]:
                self.row_plr_tcp.config(text=self.set_tyre_cmp(veh_plr[8]))

                self.row_f_03_tcp.config(text=self.set_tyre_cmp(veh_f_03[8]))
                self.row_f_02_tcp.config(text=self.set_tyre_cmp(veh_f_02[8]))
                self.row_f_01_tcp.config(text=self.set_tyre_cmp(veh_f_01[8]))
                self.row_r_01_tcp.config(text=self.set_tyre_cmp(veh_r_01[8]))
                self.row_r_02_tcp.config(text=self.set_tyre_cmp(veh_r_02[8]))
                self.row_r_03_tcp.config(text=self.set_tyre_cmp(veh_r_03[8]))

                if self.rel_add_front > 0:
                    self.row_f_04_tcp.config(text=self.set_tyre_cmp(veh_f_04[8]))
                if self.rel_add_behind > 0:
                    self.row_r_04_tcp.config(text=self.set_tyre_cmp(veh_r_04[8]))
                if self.rel_add_front > 1:
                    self.row_f_05_tcp.config(text=self.set_tyre_cmp(veh_f_05[8]))
                if self.rel_add_behind > 1:
                    self.row_r_05_tcp.config(text=self.set_tyre_cmp(veh_r_05[8]))
                if self.rel_add_front > 2:
                    self.row_f_06_tcp.config(text=self.set_tyre_cmp(veh_f_06[8]))
                if self.rel_add_behind > 2:
                    self.row_r_06_tcp.config(text=self.set_tyre_cmp(veh_r_06[8]))

            # Time gap
            self.row_plr_gap.config(text=veh_plr[5])

            self.row_f_03_gap.config(text=veh_f_03[5], fg=self.color_lapdiff(veh_f_03[6], veh_plr[6]))
            self.row_f_02_gap.config(text=veh_f_02[5], fg=self.color_lapdiff(veh_f_02[6], veh_plr[6]))
            self.row_f_01_gap.config(text=veh_f_01[5], fg=self.color_lapdiff(veh_f_01[6], veh_plr[6]))
            self.row_r_01_gap.config(text=veh_r_01[5], fg=self.color_lapdiff(veh_r_01[6], veh_plr[6]))
            self.row_r_02_gap.config(text=veh_r_02[5], fg=self.color_lapdiff(veh_r_02[6], veh_plr[6]))
            self.row_r_03_gap.config(text=veh_r_03[5], fg=self.color_lapdiff(veh_r_03[6], veh_plr[6]))

            if self.rel_add_front > 0:
                self.row_f_04_gap.config(text=veh_f_04[5], fg=self.color_lapdiff(veh_f_04[6], veh_plr[6]))
            if self.rel_add_behind > 0:
                self.row_r_04_gap.config(text=veh_r_04[5], fg=self.color_lapdiff(veh_r_04[6], veh_plr[6]))
            if self.rel_add_front > 1:
                self.row_f_05_gap.config(text=veh_f_05[5], fg=self.color_lapdiff(veh_f_05[6], veh_plr[6]))
            if self.rel_add_behind > 1:
                self.row_r_05_gap.config(text=veh_r_05[5], fg=self.color_lapdiff(veh_r_05[6], veh_plr[6]))
            if self.rel_add_front > 2:
                self.row_f_06_gap.config(text=veh_f_06[5], fg=self.color_lapdiff(veh_f_06[6], veh_plr[6]))
            if self.rel_add_behind > 2:
                self.row_r_06_gap.config(text=veh_r_06[5], fg=self.color_lapdiff(veh_r_06[6], veh_plr[6]))

            # Vehicle in pit
            if self.wcfg["show_pit_status"]:
                self.row_plr_pit.config(self.set_pitstatus(veh_plr[7]))

                self.row_f_03_pit.config(self.set_pitstatus(veh_f_03[7]))
                self.row_f_02_pit.config(self.set_pitstatus(veh_f_02[7]))
                self.row_f_01_pit.config(self.set_pitstatus(veh_f_01[7]))
                self.row_r_01_pit.config(self.set_pitstatus(veh_r_01[7]))
                self.row_r_02_pit.config(self.set_pitstatus(veh_r_02[7]))
                self.row_r_03_pit.config(self.set_pitstatus(veh_r_03[7]))

                if self.rel_add_front > 0:
                    self.row_f_04_pit.config(self.set_pitstatus(veh_f_04[7]))
                if self.rel_add_behind > 0:
                    self.row_r_04_pit.config(self.set_pitstatus(veh_r_04[7]))
                if self.rel_add_front > 1:
                    self.row_f_05_pit.config(self.set_pitstatus(veh_f_05[7]))
                if self.rel_add_behind > 1:
                    self.row_r_05_pit.config(self.set_pitstatus(veh_r_05[7]))
                if self.rel_add_front > 2:
                    self.row_f_06_pit.config(self.set_pitstatus(veh_f_06[7]))
                if self.rel_add_behind > 2:
                    self.row_r_06_pit.config(self.set_pitstatus(veh_r_06[7]))

        # Update rate
        self.after(self.wcfg["update_delay"], self.update_data)

    # Additional methods
    def color_lapdiff(self, nlap, player_nlap):
        """Compare lap differences & set color"""
        if nlap > player_nlap:
            color = self.wcfg["font_color_laps_ahead"]
        elif nlap < player_nlap:
            color = self.wcfg["font_color_laps_behind"]
        else:
            color = self.wcfg["font_color_same_lap"]
        return color

    def set_tyre_cmp(self, tc_index):
        """Substitute tyre compound index with custom chars"""
        if tc_index:
            ftire = self.wcfg["tyre_compound_list"][tc_index[0]:(tc_index[0]+1)]
            rtire = self.wcfg["tyre_compound_list"][tc_index[1]:(tc_index[1]+1)]
            tire_cmpd = f"{ftire}{rtire}"
        else:
            tire_cmpd = ""
        return tire_cmpd

    def set_pitstatus(self, pits):
        """Compare lap differences & set color"""
        if pits > 0:
            status = {"text":self.wcfg["pit_status_text"], "bg":self.wcfg["bkg_color_pit"]}
        else:
            status = {"text":"", "bg":self.cfg.overlay["transparent_color"]}
        return status

    def set_class_style(self, vehclass_name):
        """Compare vehicle class name with user defined dictionary"""
        if vehclass_name == "":
            class_config = {"text":"", "bg":self.wcfg["bkg_color_class"]}
        else:
            class_config = {"text":vehclass_name[:self.cls_width],
                            "bg":self.wcfg["bkg_color_class"]}

        for key, value in self.vehcls.classdict_user.items():
            # If class name matches user defined class
            if vehclass_name == key:
                # Assign new class name from user defined value
                short_name = value
                for subkey, subvalue in short_name.items():
                    # Assign corresponding background color
                    class_config = {"text":subkey, "bg":subvalue}
                    break

        return class_config
