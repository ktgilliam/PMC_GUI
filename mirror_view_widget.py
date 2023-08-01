from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import ObjectProperty, NumericProperty, BooleanProperty, ListProperty, BoundedNumericProperty, StringProperty
from kivy.uix.widget import Widget

import tkinter as tk
from tkinter import filedialog
import csv
from colormap import ColorMap as cmap

    
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
    enabled = BooleanProperty(False)
    _firstTime = True
    mag_value = NumericProperty(0, rebind=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if TecWidget._firstTime:
            TecWidget.rho_max = 0
            TecWidget._firstTime = False
        if self.rho_phys > TecWidget.rho_max:
            TecWidget.rho_max = self.rho_phys
        
    def connect_mirror_circle(self, mc):
        self.mirror_circle_prop = mc
    
    def activate_self(self):
        ctrlPanel = self.parent.parent
        ctrlPanel.active_tec = self
        ctrlPanel.load_field_values(self)
        pass
    
    # def on_mag_value(self, value):
    #     pass
    
    # def update_value(self, value):
    #     self.mag_value = value
        
class MirrorCircleWidget(Widget):
    diameter = NumericProperty(0)
    def on_diameter(self, instance, value):
        pass
    
class MirrorViewWidget(AnchorLayout):
    tec_cfg_list = ListProperty([])
    diameter = NumericProperty()
    cfg_file_path = StringProperty('')
    # tec_cfg_list = []
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        MirrorViewWidget.instance = self
        
    def readCsv():
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV File", ".csv")])
        print(file_path)
        cfg_list = []
        if len(MirrorViewWidget.instance.tec_cfg_list) > 0:
            MirrorViewWidget.resetTecWidgets()
        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    tec_no = int(row['TEC'])
                    theta = float(row['theta'])
                    rho_phys = float(row['rho'])
                    enabled = bool(row['enabled'])
                    cfg_list.append((tec_no, theta, rho_phys, enabled))
        except FileNotFoundError:
            return
        MirrorViewWidget.cfg_file_path = file_path
        MirrorViewWidget.instance.tec_cfg_list = cfg_list
        MirrorViewWidget.instance.populateTecWidgets()

    def resetTecWidgets():
        MirrorViewWidget.instance.tec_cfg_list = []
        rmList = []
        for child in MirrorViewWidget.instance.children:
            if type(child) == TecWidget:
                rmList.append(child)
        for child in rmList:
            MirrorViewWidget.instance.remove_widget(child)
        MirrorViewWidget.instance.parent.cfg_loaded = False
        MirrorViewWidget.instance.parent.active_tec = None
        
    def populateTecWidgets(self):
        for tec in self.tec_cfg_list:
            tw = TecWidget(id_no=tec[0], theta=tec[1], rho_phys=tec[2], enabled=tec[3])
            tw.connect_mirror_circle(self)
            tw.id = 'TEC'+str(tec[0])
            self.add_widget(tw)
        self.parent.cfg_loaded = True
        
    def on_height(self, instance, value):
        pass
    
    def enableAll(self, flag):
        for child in MirrorViewWidget.instance.children:
            if type(child) == TecWidget:
                child.enabled = flag
                
    def update_tec_map():
        for child in MirrorViewWidget.instance.children:
            if type(child) == TecWidget:
                pass
            
    def all_to_zero(self):
        for child in self.children:
            if type(child) == TecWidget:
                child.mag_value = 0.0
             
class MirrorViewControlPanel(GridLayout):
    active_tec = ObjectProperty(None,  allownone=True)
    opts_disabled = BooleanProperty(True)
    cfg_loaded = BooleanProperty(False)
    
    def setTecEnabledState(self, active):
        self.active_tec.enabled = active
        
    def update_tec_color(self, val):
        self.active_tec.mag_value = val
        # pass
        
    def clear_fields(self):
        cmd_fld = self.ids['cmd_input']
        cmd_fld.text = '0.0'
        
    def load_field_values(self, tec):
        cmd_fld = self.ids['cmd_input']
        cmd_fld.text = str(tec.mag_value)