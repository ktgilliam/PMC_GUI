from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import ObjectProperty, NumericProperty, BooleanProperty, ListProperty, BoundedNumericProperty, StringProperty
from kivy.uix.widget import Widget

import tkinter as tk
from tkinter import filedialog
from tkinter.filedialog import asksaveasfile
import csv
from colormap import ColorMap as cmap
from zernpy import ZernPol
import math
import os
import time
from tec_iface import *

class TecConfiguration():
    tec_enabled = BooleanProperty()
    tec_power_cmd = NumericProperty()
    tec_temp_diff = NumericProperty()
    
class TecWidget(Widget):
    id_no = NumericProperty(0)
    spot_diameter = NumericProperty(15)
    rho_norm = BoundedNumericProperty(0, min=0, max=10)
    rho = NumericProperty()
    rho_phys = NumericProperty(0)
    theta = NumericProperty(0)
    x_loc = NumericProperty(rebind=True)
    y_loc = NumericProperty(rebind=True)
    x_loc_abs = NumericProperty(rebind=True)
    y_loc_abs = NumericProperty(rebind=True)
    spot_rgb = ListProperty([0,1,0])
    mirror_circle_prop = ObjectProperty(rebind=True)
    mirror_px_radius = NumericProperty(rebind=True)
    enabled = BooleanProperty(False)
    mag_value = NumericProperty(0, rebind=True)
    tec_found = BooleanProperty(False)
    tec_name_str = StringProperty()
    tec_label_str = StringProperty('--')
    tec_config = None

    def connect_mirror_circle(self, mc):
        self.mirror_circle_prop = mc
    
    def activate_self(self):
        ctrlPanel = self.parent.parent
        ctrlPanel.active_tec = self
        ctrlPanel.load_field_values(self)
        pass

    
    def update_mag_value(self, value):
        self.mag_value = float(value)
        # if abs(value) > abs(TecWidget.max_mag):
        #     TecWidget.max_mag = abs(value)
        
class MirrorCircleWidget(Widget):
    diameter = NumericProperty(0)
    def on_diameter(self, instance, value):
        pass
    
class MirrorViewWidget(AnchorLayout):
    tec_cfg_list = ListProperty([])
    diameter = NumericProperty()
    cfg_file_path = StringProperty('')
    mirror_name = StringProperty('--')
    tec_widget_list = []
    # tec_cfg_list = []
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        MirrorViewWidget.instance = self
        
    def readMirrorConfigCsv():
        # root = tk.Tk()
        # root.withdraw()
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV File", ".csv")])
        print(file_path)
        try:
            mirror_file_name = os.path.basename(file_path)
        except TypeError:
            return
        parts = mirror_file_name.split('_')
        MirrorViewWidget.instance.mirror_name = parts[0]
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
        except KeyError:
            print("Key Error - Invalid config file.")
            return
        except FileNotFoundError:
            return
        MirrorViewWidget.cfg_file_path = file_path
        MirrorViewWidget.instance.tec_cfg_list = cfg_list
        MirrorViewWidget.instance.populateTecWidgets()

        
    def readCommandCsv():
        # root = tk.Tk()
        # root.withdraw()
        mvw = MirrorViewWidget.instance
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV File", ".csv")])
        print(file_path)
        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                tec_cmds = []
                for row in reader:
                    tec_no = int(row['TEC'])
                    tec_cmd = float(row['cmd'])
                    enabled = int(row['enabled'])==1
                    tec_cmd = (tec_no, tec_cmd, enabled)
                    tec_cmds.append(tec_cmd)
                    print(', '.join(row))
        except TypeError:
            return
        except KeyError:
            print("Input file not formatted correctly (KeyError)")
            return
        except FileNotFoundError:
            return
        mvw.applyTecCommands(tec_cmds)
        mvw.parent.updateActiveTecFields()
        
    def applyTecCommands(self, cmds):
        for cmd in cmds:
            tecNo = cmd[0]
            val = cmd[1]
            tecWidget = self.get_tec_by_no(tecNo)
            tecWidget.update_mag_value(val)
            tecWidget.enabled = cmd[2] and tecWidget.tec_found
            pass
        
    def saveCommandCsv():    
        mvw = MirrorViewWidget.instance
        date_str = time.strftime('%Y_%m_%d_%H_%M_%S')
        newFileNameSuggestion = mvw.mirror_name+'_cmds_'+date_str
        f = asksaveasfile(initialfile = newFileNameSuggestion, defaultextension=".csv",filetypes=[("All Files","*.*"),("CSV Documents","*.csv")])
        rows = []
        rows.append(['TEC', 'cmd', 'enabled'])
        for cfg in mvw.tec_cfg_list:
            tecNo = cfg[0]
            tecWidget = mvw.get_tec_by_no(tecNo)
            val = tecWidget.mag_value
            en = int(tecWidget.enabled)
            row = [tecNo, val, en]
            rows.append(row)
        with open(f.name, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
    
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
        rho_max = 0.0
        for cfg in self.tec_cfg_list:
            rho = cfg[2]
            if rho > rho_max:
                rho_max = rho

        for cfg in self.tec_cfg_list:
            rho_phys=cfg[2]
            rho_norm = rho_phys/rho_max
            tw = TecWidget(id_no=cfg[0], theta=cfg[1],rho_norm=rho_norm , enabled=cfg[3])
            tw.connect_mirror_circle(self)
            tw.id = 'TEC'+str(cfg[0])
            tw.tec_name_str = tw.id
            tw.enabled = False
            self.add_widget(tw)
            self.tec_widget_list.append(tw)
        self.parent.cfg_loaded = True
        
    def on_height(self, instance, value):
        pass
    
    def enableAll(self, flag):
        for child in MirrorViewWidget.instance.children:
            if type(child) == TecWidget:
                child.enabled = flag
                
    def update_tec_map(self):
        for child in MirrorViewWidget.instance.children:
            if type(child) == TecWidget:
                pass
            
    def all_to_zero(self):
        for child in self.children:
            if type(child) == TecWidget:
                child.mag_value = 0.0
    
    def get_tec_polar_centroids(self):
        centroid_list = []
        for child in self.children:
            if type(child) == TecWidget:
                centroid = [child.rho_norm*2, child.theta]
                centroid_list.append(centroid)
        return centroid_list

    def get_tec_by_no(self, no):
        for child in self.children:
            if type(child) == TecWidget:
                if child.id_no == no:
                    return child
        return None
    
    def get_tec_val(self, no):
        tec = self.get_tec_by_no(no)
        if tec is not None:
            return tec.mag_value
        
    def zernike_command(self, osa_idx, theta_offs=0.0, scale=1):
        # Note: This is not that simple - the mag_value will need to come from a surface fit with the influence functions
        theta_offs = theta_offs*math.pi/180
        zp = ZernPol(osa_index=osa_idx)
        cnt = 0
        for child in self.children:
            if type(child) == TecWidget:
                theta = (child.theta+theta_offs) % (2*math.pi)
                Z = zp.polynomial_value(child.rho_norm, theta, use_exact_eq=True)
                new_mag = 0.5*Z*scale
                new_mag = round(new_mag, 12)
                child.update_mag_value(new_mag)
                cnt = cnt + 1
    
class MirrorViewControlPanel(GridLayout):
    active_tec = ObjectProperty(None,  allownone=True)
    opts_disabled = BooleanProperty(True)
    cfg_loaded = BooleanProperty(False)
    
    def setTecEnabledState(self, active):
        if self.active_tec.tec_found:
            self.active_tec.enabled = active
        
    def enable_found_tecs(self, found_tec_cfg_list):
        mvw = self.ids['mvw']
        for found_tec_cfg in found_tec_cfg_list:
            found_tec_no = found_tec_cfg.tecNo
            tec_widget = mvw.get_tec_by_no(found_tec_no)
            if tec_widget is not None:
                tec_widget.tec_config = found_tec_cfg
                tec_widget.tec_found = True
                tec_widget.enabled = True
            pass
        pass
        
    def update_tec_color(self, val):
        if self.active_tec is not None:
            self.active_tec.update_mag_value(val)
        # pass
        
    def clear_fields(self):
        cmd_fld = self.ids['cmd_input']
        cmd_fld.text = '0.0'
        
    def load_field_values(self, tec):
        cmd_fld = self.ids['cmd_input']
        cmd_fld.text = str(tec.mag_value)
        cmd_fld.cursor = (0,0)
        
    def map_zernike(self):
        mvw = self.ids['mvw']
        zp = self.ids['zernike_panel']
        mvw.zernike_command(zp.j, zp.theta_offset, zp.scale_coeff)
        self.updateActiveTecFields()
        
    def check_if_tec_is_found(self, tecNo):
        mvw = self.ids['mvw']
        tec = mvw.get_tec_by_no(tecNo)
        return tec.tec_found
    
    def check_if_tec_is_enabled(self, tecNo):
        mvw = self.ids['mvw']
        tec = mvw.get_tec_by_no(tecNo)
        return tec.enabled
        
    def getFieldValue(self, tecNo):
        mvw = self.ids['mvw']
        val = mvw.get_tec_val(tecNo)
        gain_fld = self.ids['gain_input']
        cmd = val * gain_fld.value
        return cmd
    
    def updateActiveTecFields(self):
        if self.active_tec is not None:
            self.load_field_values(self.active_tec)
    
class Zernike_Widget(GridLayout):
    j = NumericProperty(0)
    n = NumericProperty(0)
    m = NumericProperty(0)
    theta_offset = NumericProperty(0)
    scale_coeff = NumericProperty(1.0)
    name = StringProperty(' (Piston)')
    
    def check_inputs(self):
        pass
    
    def increment(self):
        self.j = self.j+1
        
    def decrement(self):
        if self.j > 0:
            self.j = self.j-1
        else:
            self.j = 0
            
    def update_name(self):
        if self.j == 0:
            name_str = 'Piston'
        else:
            zp = ZernPol(osa_index=self.j)
            name_str = zp.get_polynomial_name()
        self.name = " (" + name_str + ")"
        
