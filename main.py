from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy_plotter.plot import Plot, Series
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty, NumericProperty
from kivy.uix.scrollview import ScrollView
from data_models import TransientDataFile, BehaviorDataFile
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout

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
    

class ListBox(ScrollView):
    layout = ObjectProperty(None)
    scroll_pos = NumericProperty(0)
    scroll_size = NumericProperty(200)

    def __init__(self, **kwargs):
        super(ListBox, self).__init__(**kwargs)
        
    def item_info(self):
        self.itemname = GetItemName()
        popup = Popup(title='Create New Parameter', content = self.itemname, size_hint=(.4,.4))
        self.itemname.bind(ok = popup.dismiss)
        popup.bind(on_dismiss = self.build)
        popup.open()
        
    def build(self, *largs):
        itemsetup = ItemSetup()
        if self.itemname.text == '':
            itemsetup.item_info = 'Default'
        else:
            itemsetup.item_info = self.itemname.text
        self.layout.add_widget(itemsetup)
        self.layout.bind(minimum_height=self.layout.setter('height'))

    def scrolling(self, value):
        view_size = self.size[1]
        self.scroll_pos = value[0] * view_size
        self.scroll_size = value[1] * view_size

    def move_scroll_y(self, touch_y):
        grab_location = touch_y - self.scroll_pos - self.pos[1]
        self.scroll.scroll_y = (touch_y - self.pos[1] + grab_location)/self.size[1]

class ScrollBar(Widget):
    def __init__(self, **kwargs):
        super(ScrollBar, self).__init__(**kwargs) 
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            return True

    def on_touch_move(self, touch):
        if touch.grab_current == self:
            self.parent.parent.move_scroll_y(touch.pos[1])
            return True

    def on_touch_up(self, touch):
        if touch.grab_current == self:
            return True

class GetItemName(Widget):
    
    ok = BooleanProperty(False)
    text = StringProperty("")

    def __init__(self, **kwargs):
        super(GetItemName, self).__init__(**kwargs)

class ItemSetup(BoxLayout):
    item_info = StringProperty('')
    item_state = StringProperty('normal')

    def __init__(self, **kwargs):
        super(ItemSetup, self).__init__(**kwargs)

    def remove_item(self):
        self.parent.remove_widget(self)
        
    def item_callback(self):
        if self.item_state == 'normal':
            self.item_state = 'down'
        else:
            self.item_state = 'normal'

if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainView())