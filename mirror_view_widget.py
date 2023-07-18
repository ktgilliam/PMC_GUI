from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty, ListProperty, DictProperty
from kivy.uix.widget import Widget

import tkinter as tk
from tkinter import filedialog
import csv

class TecInfoPanel(GridLayout):
    pass

class TecWidget(Widget):
    id_no = NumericProperty(0)
    diameter = NumericProperty(15)
    rho_norm = NumericProperty()
    rho_max = NumericProperty()
    rho = NumericProperty()
    theta = NumericProperty(0)
    x_loc = NumericProperty()
    y_loc = NumericProperty()
    x_loc_abs = NumericProperty()
    y_loc_abs = NumericProperty()
    spot_rgb = ListProperty([1,0,0])

class MirrorCircleWidget(Widget):
    diameter = NumericProperty(100)

class MirrorViewWidget(AnchorLayout):
    def readCsv():
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV File", ".csv")])
        print(file_path)
        try:
            with open(file_path, newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
                tec_cmds = []
                headerRow = True
                for row in spamreader:
                    if headerRow:
                        headerRow = False
                        continue
                    # tec_no = int(row[0])
                    # tec_cmd = float(row[1])
                    # tec_cmd = (tec_no, tec_cmd)
                    # tec_cmds.append(tec_cmd)
                    # print(', '.join(row))
        except FileNotFoundError:
            return



class MirrorViewControlPanel(GridLayout):
    pass