from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.uix.widget import Widget

class TecWidget(Widget):
    pass

class MirrorWidget(Widget):
    diameter = NumericProperty(100)

class MirrorViewWidget(AnchorLayout):
    pass

class MirrorViewControlPanel(GridLayout):
    pass