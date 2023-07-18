from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.uix.widget import Widget

class TecWidget(Widget):
    pass

class MirrorViewWidget(RelativeLayout):
    diameter = NumericProperty(100)
    
class MirrorViewControlPanel(GridLayout):
    pass