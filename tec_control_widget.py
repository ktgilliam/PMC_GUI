from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from tec_luts import *

tmp_num_tecs = 132

class TECField(GridLayout):
    tec_no = NumericProperty()
    def __init__(self, tec_no, **kwargs): 
        super().__init__(**kwargs)
        self.tec_no = tec_no

class TECFieldList(GridLayout):
    num_tec = NumericProperty()
    
    def __init__(self, **kwargs): 
        super(TECFieldList, self).__init__(**kwargs)
        self.num_tec = tmp_num_tecs
        # layout = self.ids['fields']
        # for ii in range(self.num_tec):
        #     tf = TECField(ii+1)
        #     layout.add_widget(tf)
            
    def createFields(self):
        self.height = self.num_tec * 55 / self.cols
        for ii in range(self.num_tec):
            tf = TECField(tec_no=ii+1, width = (self.parent.width-60)/self.cols)
            self.add_widget(tf)
            
class TECControlWidget(GridLayout):
    def __init__(self, **kwargs): 
        super().__init__(**kwargs)
        
    def loadList(self):
        list = self.ids['tec_field_list']
        list.createFields()
        a = 5        
            
class TECController():
    def __init__(self, ctrlWidget, nursery, debugMode = False, **kwargs): 
        self.nursery = nursery
        self.controllerWidget = ctrlWidget
        self.debugMode = debugMode
    
