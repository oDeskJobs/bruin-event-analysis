from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy_plotter.plot import Plot, Series
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty, ListProperty
from kivy.uix.scrollview import ScrollView
from data_models import TransientDataFile, BehaviorDataFile
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout 
from kivy.factory import Factory 

from kivy.uix.gridlayout import GridLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.clock import Clock
import os

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

class VariablePairer(BoxLayout):
    current_pick_1 = ObjectProperty(None)
    current_pick_2 = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(VariablePairer, self).__init__(**kwargs)




class VariablesList(GridLayout):
    variable_list = ListProperty(('1', '2', '3', '4', '5'))
    current_buttons = ListProperty([])
    current_toggled = ListProperty([])
    current_radio_button = ObjectProperty(None)
    preserve_button_state = BooleanProperty(False)
    radio_button_mode = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(VariablesList, self).__init__(**kwargs)
        self.size_hint_y = None
        Clock.schedule_once(self.init_button_list)

        Clock.schedule_once(self.append_test, 5.0)

    def clear_list(self):
        for each in self.current_buttons:
            self.remove_widget(each)
        self.current_buttons = []

    def init_button_list(self, dt):
        self.populate_list()

    def populate_list(self):
        for each in self.variable_list:
            variable_button = ToggleButton(text = each, on_press = self.button_press)
            if self.radio_button_mode == True:
                variable_button.group = self
            self.add_widget(variable_button)
            self.current_buttons.append(variable_button)
        if self.preserve_button_state == True:
            self.restore_button_state()
        self.height = len(self.variable_list) * (self.row_default_height + self.spacing)

    def restore_button_state(self):
        for each in self.current_toggled:
            for button in self.current_buttons:
                if each.text == button.text:
                    button.state = each.state
        self.reset_current_toggled_list()

    def reset_current_toggled_list(self):
        self.current_toggled = []
        for each in self.current_buttons:
            if each.state == 'down':
                self.current_toggled.append(each)


    def button_press(instance, value):
        if value.state == 'down':
            value.parent.current_toggled.append(value)
            if value.parent.radio_button_mode == True:
                value.parent.current_radio_button = value
        if value.state == 'normal':
            value.parent.current_toggled.remove(value)


    def on_variable_list(self, instance, value):
        self.clear_list()
        self.canvas.clear()
        self.populate_list()

    def append_test(self, dt):
        self.variable_list.append('6')

class VariablePairsBox(BoxLayout):
    layout = ObjectProperty(None)
    variable_pairs = ListProperty([])

    def __init__(self, **kwargs):
        super(VariablePairsBox, self).__init__(**kwargs)

    def get_variable_pair(self):
        self.variable_pairer =VariablePairer()
        popup = Popup(title='Choose Variable Pairs', content = self.variable_pairer, size_hint = (.6, .6))
        self.variable_pairer.dismiss_button.bind(on_press = popup.dismiss)
        popup.bind(on_dismiss = self.build_pair)
        popup.open()

    def on_variable_pairs(self, instance, value):
        self.layout.height = (len(self.variable_pairs) + 1) * self.layout.spacing

    def build_pair(self, *largs):
        variable_pair = VariablePair()
        variable_pair.parent_variable_box = self
        if self.variable_pairer.current_pick_1 != None:
            variable_one = self.variable_pairer.current_pick_1.text
            variable_pair.variable_one = variable_one
        if self.variable_pairer.current_pick_2 != None:
            variable_two = self.variable_pairer.current_pick_2.text
            variable_pair.variable_two = variable_two

        self.layout.add_widget(variable_pair)
        self.variable_pairs.append(variable_pair)
        


class ListBox(BoxLayout):
    layout = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ListBox, self).__init__(**kwargs)

    def get_directions(self):
        self.directions = LoadSave()
        popup = Popup(title='Load Existing or Save New?', content = self.directions, size_hint=(.4,.4))
        self.directions.bind(ok = popup.dismiss)
        popup.open()

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

class VariableBox(BoxLayout):
    variable_list = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(VariableBox, self).__init__(**kwargs)

class VariablePair(BoxLayout):
    variable_one = StringProperty("Default 1")
    variable_two = StringProperty("Default 2")
    toggle_button = ObjectProperty(None)
    parent_variable_box = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(VariablePair, self).__init__(**kwargs)

    def on_variable_one(self, instance, value):
        self.toggle_button.text = self.variable_one + ' x ' + self.variable_two

    def on_variable_two(self, instance, value):
        self.toggle_button.text = self.variable_one + ' x ' + self.variable_two

    def remove_item(self):
        self.parent.remove_widget(self)
        self.parent_variable_box.variable_pairs.remove(self)

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

class LoadSave(Widget):
    ok = BooleanProperty(False)
    text = StringProperty("")
    loadfile = ObjectProperty(None)
    savefile = ObjectProperty(None)
    text_input = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(LoadSave, self).__init__(**kwargs)

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def show_save(self):
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        with open(os.path.join(path, filename[0])) as stream:
            self.text_input.text = stream.read()

        self.dismiss_popup()

    def save(self, path, filename):
        with open(os.path.join(path, filename), 'w') as stream:
            stream.write(self.text_input.text)

        self.dismiss_popup()

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    filechooser = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(LoadDialog, self).__init__(**kwargs)
        # for now just default to user's home directory. In the future, we may want to
        # add some code to go to the same directory the user was in last time.
        self.filechooser.path = os.path.expanduser('~')


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)
    filechooser = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SaveDialog, self).__init__(**kwargs)
        # for now just default to user's home directory. In the future, we may want to
        # add some code to go to the same directory the user was in last time.
        self.filechooser.path = os.path.expanduser('~')

Factory.register('LoadSave', cls=LoadSave)
Factory.register('LoadDialog', cls=LoadDialog)
Factory.register('SaveDialog', cls=SaveDialog)

if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainView())