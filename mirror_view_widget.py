from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.uix.widget import Widget

class TecWidget(Widget):
    diameter = NumericProperty(15)
    rho = NumericProperty()
    theta = NumericProperty(0)
    x_loc = NumericProperty()
    y_loc = NumericProperty()
    

class MirrorWidget(Widget):
    diameter = NumericProperty(100)

class MirrorViewWidget(AnchorLayout):
    pass

class MirrorViewControlPanel(GridLayout):
    pass