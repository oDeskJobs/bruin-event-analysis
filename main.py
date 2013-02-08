from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy_plotter.plot import Plot 
from kivy.properties import ObjectProperty
from kivy.uix.button import Button

Builder.load_file('ui.kv')

class MainView(Widget):
    visualizer = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(MainView, self).__init__(**kwargs)
        
        self.setup_visualizer()


    def setup_visualizer(self):
        v = self.visualizer
        v.border_width = 2
        v.border_color = (.7, .7, .7)
        v.tick_color = (.7, .7, .7)
        v.y_axis_title = "DA Transient Amplitude (nM)"
        v.x_axis_title = "Time (sec)"
        v.viewport = [0,0,50,100]
        v.tick_distance_x = 10
        v.tick_distance_y = 20



class ListBox(Widget):
    pass

if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainView())