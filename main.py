from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy_plotter.plot import Plot, Series
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from data_models import TransientDataFile, BehaviorDataFile

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
        v.tick_distance_x = 30
        v.tick_distance_y = 20

        

    def load_transients(self):
        t = TransientDataFile('sample data/CV5_Inst5aSuc_DATransientData.csv')
        self.transients = Series(self.visualizer, fill_color = (.68, .42, .73), ick_width = 4, tick_height = 15)

        data = [p for p in t.get_xy_pairs()]
        self.transients.data = data
        self.transients.marker = 'tick'
        self.transients.resize_plot_from_data()
        self.transients.enable()
        
    def load_behavior(self):
        b = BehaviorDataFile('sample data/Example_BehaviorData with more variables.csv', 'sample data/Example_BehaviorData with more variables.schema')
        self.behaviors = Series(self.visualizer, fill_color = (.13, .24, .62), marker = 'plus', tick_height = 20, tick_width = 5)
        # we definitely want a better way of handling Boolean data than just assigning it a hardcoded y value like this
        data = [(p[0], 50) for p in b.get_xy_pairs(x='Left Lever Press')]
        self.behaviors.data = data
        self.behaviors.enable()

class ListBox(Widget):
    pass

if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainView())