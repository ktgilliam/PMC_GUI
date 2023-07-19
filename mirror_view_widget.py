from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty, ListProperty, DictProperty, BoundedNumericProperty
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
    rho_norm = BoundedNumericProperty(0, min=-0.5, max=0.5)
    rho_max = NumericProperty(rebind=True, allownone=True)
    rho = NumericProperty()
    theta = NumericProperty(0)
    x_loc = NumericProperty()
    y_loc = NumericProperty()
    x_loc_abs = NumericProperty()
    y_loc_abs = NumericProperty()
    spot_rgb = ListProperty([0,1,0])
    mirror_circle_prop = ObjectProperty(rebind=True)
    # mirror_circle_prop = ObjectProperty()
    
    def connect_mirror_circle(self, mc):
        self.mirror_circle_prop = mc
        tmp = mc.property('diameter')
        # test = self.mirror_circle_prop.diameter
        # self.bind(rho_max=self.mirror_circle_prop.setter('diameter'))
        self.bind(rho_max=mc.setter('diameter'))
        pass
    
    def on_rho_max(self, instance, value):
        pass
    
    
    # def on_mirror_circle_prop(self, instance, mcw):
    #     self.rho_max = mcw.diameter
    #     pass
    
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
        try:
            with open(file_path, newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
                headerRow = True
                for row in spamreader:
                    if headerRow:
                        headerRow = False
                        continue
                    tec_no = int(row[0])
                    theta = float(row[1])
                    rho_norm = float(row[2])
                    centroid_list.append((tec_no, theta, rho_norm))
                    pass
        except FileNotFoundError:
            return
        MirrorViewWidget.instance.tec_centroid_list = centroid_list
        MirrorViewWidget.instance.populateTecWidgets()
        
    def populateTecWidgets(self):
        mc = MirrorViewWidget.instance.ids['mirror_circle']
        for tec in self.tec_centroid_list:
            tf = TecWidget(id_no=tec[0], theta=tec[1], rho_norm=tec[2])
            # tf.rho_max = self.diameter
            # tf.bind(rho_max=self.setter('diameter'))
            tf.connect_mirror_circle(self)
            self.ids['TEC'+str(tec[0])] = tf
            self.add_widget(tf)
            
    # def on_height(self, instance, value):
    #     pass
    
class MirrorViewControlPanel(GridLayout):
    pass