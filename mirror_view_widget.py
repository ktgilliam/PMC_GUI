from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import ObjectProperty, NumericProperty, BooleanProperty, ListProperty, BoundedNumericProperty
from kivy.uix.widget import Widget

import tkinter as tk
from tkinter import filedialog
import csv

class TecConfiguration():
    tec_enabled = BooleanProperty()
    tec_power_cmd = NumericProperty()
    tec_temp_diff = NumericProperty()

class TecWidget(Widget):
    id_no = NumericProperty(0)
    spot_diameter = NumericProperty(15)
    rho_norm = BoundedNumericProperty(0, min=0, max=1)
    rho = NumericProperty()
    rho_phys = NumericProperty(0)
    theta = NumericProperty(0)
    x_loc = NumericProperty()
    y_loc = NumericProperty()
    x_loc_abs = NumericProperty()
    y_loc_abs = NumericProperty()
    spot_rgb = ListProperty([0,1,0])
    mirror_circle_prop = ObjectProperty(rebind=True)
    mirror_px_dia = NumericProperty(rebind=True)
    rho_max = NumericProperty(0, rebind=True, allownone=True)
    _firstTime = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if TecWidget._firstTime:
            TecWidget.rho_max = 0
            TecWidget._firstTime = False
        if self.rho_phys > TecWidget.rho_max:
            TecWidget.rho_max = self.rho_phys
        
    def connect_mirror_circle(self, mc):
        self.mirror_circle_prop = mc
    
class MirrorCircleWidget(Widget):
    diameter = NumericProperty(0)
    def on_diameter(self, instance, value):
        pass
    
class MirrorViewWidget(AnchorLayout):
    tec_centroid_list = ListProperty([])
    diameter = NumericProperty()
    # tec_centroid_list = []
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        MirrorViewWidget.instance = self
        
    def readCsv():
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV File", ".csv")])
        print(file_path)
        centroid_list = []
        if len(MirrorViewWidget.instance.tec_centroid_list) > 0:
            MirrorViewWidget.resetTecWidgets()
        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    tec_no = int(row['TEC'])
                    theta = float(row['theta'])
                    rho_phys = float(row['rho'])
                    centroid_list.append((tec_no, theta, rho_phys))
        except FileNotFoundError:
            return
        MirrorViewWidget.instance.tec_centroid_list = centroid_list
        MirrorViewWidget.instance.populateTecWidgets()

    def resetTecWidgets():
        MirrorViewWidget.instance.tec_centroid_list = []
        rmList = []
        for child in MirrorViewWidget.instance.children:
            if type(child) == TecWidget:
                rmList.append(child)
        for child in rmList:
            MirrorViewWidget.instance.remove_widget(child)
            
    def populateTecWidgets(self):
        
        for tec in self.tec_centroid_list:
            tf = TecWidget(id_no=tec[0], theta=tec[1], rho_phys=tec[2])
            tf.connect_mirror_circle(self)
            tf.id = 'TEC'+str(tec[0])
            self.add_widget(tf)
            
    def on_height(self, instance, value):
        pass
    
class MirrorViewControlPanel(GridLayout):
    pass