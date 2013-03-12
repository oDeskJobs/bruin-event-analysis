from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy_plotter.plot import Plot
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty, ListProperty, NumericProperty
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout 
from kivy.factory import Factory 
from kivy.uix.gridlayout import GridLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.clock import Clock

from double_slider import DoubleSlider
from data_models import TransientDataFile, BehaviorDataFile
from util import SeriesController, Workspace, Subject, Session

import os

Builder.load_file('ui.kv')


def get_bout_regions_from_xy_data(data, bout_threshold = 1.):
    sorted_data = sorted(data, key=lambda x: x[0])
    in_bout = False
    current_bout_start = 0
    bouts = []
    x1 = sorted_data[0]
    for x2 in sorted_data[1:]:
        within_threshold = (x2[0]-x1[0] <= bout_threshold)
        if not in_bout and within_threshold:
            in_bout = True
            current_bout_start = x1[0]
        elif in_bout and not within_threshold:
            bouts.append((current_bout_start, x1[0]))
            in_bout = False
        x1 = x2

    return bouts

def get_transitions_from_xy_data(data1, data2, threshold = 1.):
    data_dict = {k[0]: 1 for k in data1}
    _data_dict2 = {k[0]:2 if k not in data1 else 3 for k in data2}
    data_dict.update(_data_dict2)
    all_keys = sorted(data_dict.keys())
    print data_dict
    print all_keys
    
    cursor_in_data1 = False
    cursor_not_in_data1_until = 0
    transitions = []

    for x2 in all_keys:
        if data_dict[x2] != 1:
            if cursor_in_data1 and x2 - threshold >= x1:
                transitions.append((x1,x2))
            cursor_not_in_data1_until = x2 + threshold
            cursor_in_data1 = False
        elif data_dict[x2] == 1 and x2 > cursor_not_in_data1_until:
            cursor_in_data1 = True
        x1 = x2

    return transitions


class MainView(Widget):
    visualizer = ObjectProperty(None)
    transient_box = ObjectProperty(None)
    behavior_box = ObjectProperty(None)
    bout_id_box = ObjectProperty(None)
    transition_box = ObjectProperty(None)
    event_box = ObjectProperty(None)
    legend_box = ObjectProperty(None)
    session_box = ObjectProperty(None)
    subject_box = ObjectProperty(None)

    behavior_files = ListProperty(None)
    transient_files = ListProperty(None)
    sessions = ListProperty(None)
    current_session = ObjectProperty(None, allownone = True)
    subjects = ListProperty(None)
    current_subject = ObjectProperty(None, allownone = True)

    legend_width = NumericProperty(300)

    def __init__(self, **kwargs):
        super(MainView, self).__init__(**kwargs)
        self.transient_files = []
        self.behavior_files = []
        self.setup_visualizer()
        self.series_controller = SeriesController(self.visualizer)
        self.series_controller.bind(all_variables_list = self._all_variables_changed)

        self.session_button_list = self.session_box.listbox.variable_list
        self.session_button_list.remove_button_callback = self._remove_session_callback
        self.session_button_list.bind(current_toggled=self._session_select_changed)

        self.subject_button_list = self.subject_box.listbox.variable_list
        self.subject_button_list.remove_button_callback = self._remove_subject_callback
        self.subject_button_list.bind(current_toggled=self._subject_select_changed)
        # self.bind(subjects=self._subject_select_changed)

        self.transient_button_list = self.transient_box.listbox.variable_list
        self.transient_button_list.bind(current_toggled=self._transient_select_changed)

        self.behavior_button_list = self.behavior_box.listbox.variable_list
        self.behavior_button_list.bind(current_toggled=self._behavior_select_changed)

        self.legend_button_list = self.legend_box.listbox.variable_list
        self.legend_button_list.bind(current_toggled=self._visible_series_changed)

        self.bout_id_button_list = self.bout_id_box.listbox.variable_list
        self.bout_id_button_list.bind(current_toggled=self._bout_id_params_changed)
        self.bout_id_box.bind(bout_threshold=self._bout_id_params_changed)

        self.transition_button_list = self.transition_box.listbox.variable_list
        self.transition_button_list.bind(current_toggled=self._transition_params_changed)
        self.transition_box.bind(transition_threshold=self._transition_params_changed)

        self.event_button_list = self.event_box.listbox.variable_list
        self.event_button_list.bind(current_toggled=self._event_params_changed)
        self.event_box.bind(before_threshold=self._event_params_changed)
        self.event_box.bind(after_threshold=self._event_params_changed)

        
        self.session_box.listbox.variable_list.variable_list = []
        self.subject_box.listbox.variable_list.variable_list = []
        
        # define a function that tells which labels should come before other labels. Ensures that "Transients"
        # always appears first, and then subsequent labels are sorted by alphabetical order
        self.label_sort_func = lambda x: '0000000' if x.lower() == 'transients' else x.lower()

        self.blank_workspace = Workspace()
        self.blank_workspace.save(self)

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

    def prompt_for_transient_file(self):
        if self.current_subject is None: 
            # need a warning dialog here
            return
        LoadSave(action='load', callback=self._add_transient_file)

    def prompt_for_behavior_file(self):
        if self.current_subject is None: 
            # need a warning dialog here
            return
        LoadSave(action='load', callback=self._add_behavior_file)

    def _add_transient_file(self, path):
        try:
            t = TransientDataFile(path)
        except:
            print "Could not import %s as a transient data file. Aborting." % (path,)
            # we will want to make this visible in a popup.
            return

        if os.path.basename(t.source_file) in [os.path.basename(x.source_file) for x in self.transient_files]:
            print "%s has already been imported for this subject. Aborting." % (path,)
            return

        self.transient_files.append(t)

    def on_transient_files(self, instance, value):
        self.transient_button_list.variable_list = [os.path.basename(t.source_file) for t in self.transient_files]

    def on_behavior_files(self, instance, value):
        self.behavior_button_list.variable_list = [os.path.basename(t.source_file) for t in self.behavior_files]

    def on_sessions(self, instance, value):
        self.session_button_list.variable_list = [str(x) for x in self.sessions]

    def on_subjects(self, instance, value):
        self.subject_button_list.variable_list = [str(x) for x in self.subjects]

    def _transient_select_changed(self, instance, value):
        selected_basenames = [v.text for v in value]
        self.series_controller.clear(label = 'Transients')
        for t in self.transient_files:
            if os.path.basename(t.source_file) in selected_basenames:
                data = [p for p in t.get_xy_pairs()]
                self.series_controller.add_data('Transients', data)

    def _behavior_select_changed(self, instance, value):
        selected_basenames = [v.text for v in value]
        
        self.series_controller.clear(except_label = 'Transients')
        for s in self.behavior_files:
            if os.path.basename(s.source_file) in selected_basenames:
                for field in s.get_valid_time_columns():
                    data = [p for p in s.get_xy_pairs(x=field)]
                    self.series_controller.add_data(field, data, marker='plus', is_x_only = True)

    def _add_behavior_file(self, path):
        schema_file = os.path.splitext(path)[0] + '.schema'
        if not os.path.isfile(schema_file):
            print "No schema file present. Aborting."
            return

        try:
            t = BehaviorDataFile(path, schema_file)
        except:
            print "Could not import %s as a behavior data file. Aborting." % (path,)
            # we will want to make this visible in a popup.
            return

        if os.path.basename(t.source_file) in [os.path.basename(x.source_file) for x in self.behavior_files]:
            print "%s has already been imported for this subject. Aborting." % (path,)
            return

        self.behavior_files.append(t)
        return
        # right here we need to create a series FOR EACH VARIABLE, and have them go down to the legend pane.
        s = Series(self.visualizer, fill_color = color_palette.get_color(t.source_file), marker = 'plus', tick_height = 20, tick_width = 5)
        # we definitely want a better way of handling Boolean data than just assigning it a hardcoded y value like this
        data = [(p[0], 50) for p in t.get_xy_pairs(x='Left Lever Press')]
        print data
        s.data = data
        s.source_file = t.source_file

        self.behavior_series.append(s)
        self.behavior_files.append(t)


    def _all_variables_changed(self, instance, value):
        self.bout_id_box.listbox.variable_list.variable_list = [v for v in sorted(value, key=self.label_sort_func) if v != "Transients"]
        self.event_box.listbox.variable_list.variable_list = [v for v in sorted(value, key=self.label_sort_func) if v != "Transients"]
        self.legend_box.listbox.variable_list.variable_list = sorted(value, key=self.label_sort_func)
        self.transition_box.available_variables = sorted(value, key=self.label_sort_func)

    def _visible_series_changed(self, instance, value):
        selected_series = [v.text for v in value]
        self.series_controller.update_visible_series(selected_series)

    def _bout_id_params_changed(self, *largs):
        # put a little lag on calculate_bouts so that user can fiddle with slider without freezing things up.
        try:
            Clock.unschedule(self.calculate_bouts)
        except:
            print "couldn't unschedule"
        Clock.schedule_once(self.calculate_bouts, .2)

    def _transition_params_changed(self, *largs):
        # put a little lag on calculate_transitions so that user can fiddle with slider without freezing things up.
        try:
            Clock.unschedule(self.calculate_transitions)
        except:
            print "couldn't unschedule"
        Clock.schedule_once(self.calculate_transitions, .2)

    def _event_params_changed(self, *largs):
        # put a little lag on calculate_event_matches so that user can fiddle with slider without freezing things up.
        try:
            Clock.unschedule(self.calculate_event_matches)
        except:
            print "couldn't unschedule"
        Clock.schedule_once(self.calculate_event_matches, .2)

    def calculate_bouts(self, *largs):
        self.series_controller.clear_highlights()
        for t in self.bout_id_box.listbox.variable_list.current_toggled:
            label = t.text
            data = self.series_controller.get_data(label)
            bouts = get_bout_regions_from_xy_data(data, bout_threshold = self.bout_id_box.bout_threshold)
            print "Identified bouts for series %s:" % (label,), bouts
            self.series_controller.add_highlights(t.text, bouts)

    def calculate_transitions(self, *largs):
        self.series_controller.clear_arrows()
        for t in self.transition_box.listbox.variable_list.current_toggled:
            # split label into two variables using "->" as delimiter
            label1, label2 = [v.strip() for v in t.text.split('->')]
            data1, data2 = [self.series_controller.get_data(l) for l in (label1, label2)]
            transitions = get_transitions_from_xy_data(data1, data2, threshold = self.transition_box.transition_threshold)
            print "Identified transitions for series %s:" % (t.text,), transitions
            self.series_controller.add_arrows(label1, label2, transitions)

    def calculate_event_matches(self, *largs):
        self.series_controller.clear_col_highlights()
        for t in self.event_box.listbox.variable_list.current_toggled:
            label = t.text
            before_dist = self.event_box.before_threshold
            after_dist = self.event_box.after_threshold
            print before_dist, after_dist
            self.series_controller.add_col_highlights(label, -before_dist, after_dist)

    def add_subject(self):
        if self.current_session is None:
            # need an error message here
            return
        p = AskForTextPopup(title = "New Subject", label= "Please name this subject.", callback = self._add_subject_callback)
        p.open()

    def add_session(self):
        p = AskForTextPopup(title = "New Session", label= "Please name this session.", callback = self._add_session_callback)
        p.open()

    def _add_session_callback(self, session_name):
        if session_name.strip() == "": return
        s = Session(session_name)
        self.sessions.append(s)
        self.session_button_list.set_state(session_name, 'down')

    def _add_subject_callback(self, subject_name):
        if subject_name.strip() == "" or self.current_session is None: return
        self.current_session.add_subject(subject_name)
        self.subjects = self.current_session.subjects

    def remove_behavior_button(self):
        self.behavior_button_list.del_button_mode = True

    def remove_transient_button(self):
        self.transient_button_list.del_button_mode = True

    def _session_select_changed(self, instance, value):
        names = [v.text for v in value]

        if len(names) == 0:
            self.subjects = []
            self.current_session = None
            return

        selected_sessions = [s for s in self.sessions if s.name in names]
        assert len(selected_sessions) == 1
        self.current_session = selected_sessions[0]
        self.subjects = self.current_session.subjects

    def _subject_select_changed(self, instance, value):
        if self.current_subject is not None: self.current_subject.workspace.save(self)
        if len(value) == 0:
            self.current_subject = None
            self.blank_workspace.load(self)
        else:
            names = [v.text for v in value]
            selected_subjects = [s for s in self.subjects if s.name in names]
            assert len(selected_subjects) == 1
            self.current_subject = selected_subjects[0]
            self.current_subject.workspace.load(self)

    def remove_session_button(self):
        self.session_button_list.del_button_mode = True

    def remove_subject_button(self):
        self.subject_button_list.del_button_mode = True

    def _remove_session_callback(self, text):
        if self.current_session is not None and self.current_session.name == text:
            self.current_session = None
            self.subjects = []
        selected_sessions = [s for s in self.sessions if s.name == text]
        assert len(selected_sessions) == 1
        self.sessions.remove(selected_sessions[0])

    def _remove_subject_callback(self, text):
        if self.current_subject is not None and self.current_subject.name == text:
            self.current_subject = None
            self.blank_workspace.load(self)

        selected_subjects = [s for s in self.subjects if s.name == text]
        assert len(selected_subjects) == 1
        self.current_session.remove_subject(selected_subjects[0])
        self.subjects = self.current_session.subjects

class AskForTextPopup(Popup):

    def __init__(self, title = "Selection", label = "Please provide a value.", callback = None, **kwargs):
        assert callback is not None
        self.callback = callback

        kwargs['size_hint'] = (None, None)
        kwargs['size'] = (300, 200)
        kwargs['title'] = title
        kwargs['content'] = AskForTextPopupContent(title = title, label = label, ok_callback = self._ok_callback, cancel_callback = self._cancel_callback)

        super(AskForTextPopup, self).__init__(**kwargs)

    def _ok_callback(self, text):
        self.dismiss()
        self.callback(text)

    def _cancel_callback(self):
        self.dismiss()

class AskForTextPopupContent(Widget):
    label = StringProperty("")
    ok_callback = ObjectProperty(None)
    cancel_callback = ObjectProperty(None)
    text = StringProperty("")



class BoutIDBox(BoxLayout):
    bout_threshold = NumericProperty(1.)
    slider = ObjectProperty(None)


    def set_threshold(self, value):
        self.bout_threshold = value
        print value

class TransitionIDBox(BoxLayout):
    transition_threshold = NumericProperty(1.)
    available_variables = ListProperty([])
    variable_pairs = ListProperty([])
    listbox = ObjectProperty(None)
    slider = ObjectProperty(None)

    def set_threshold(self, value):
        self.transition_threshold = value
        print value

    def add_variable_pair(self):
        variable_pairer = VariablePairer(self.available_variables)
        popup = Popup(title='Choose Variable Pairs', content = variable_pairer, size_hint = (.6, .6))
        variable_pairer.dismiss_button.bind(on_press = popup.dismiss)
        popup.bind(on_dismiss = self.build_pair)
        popup.open()

    def on_variable_pairs(self, instance, value):
        self.listbox.variable_list.variable_list = ["%s -> %s" % (v.text, w.text) for v,w in value]

    def build_pair(self, instance):
        pick1 = instance.content.current_pick_1
        pick2 = instance.content.current_pick_2
        if pick1 is None or pick2 is None: return

        self.variable_pairs.append((pick1, pick2))

    def remove_button_callback(self):
        self.listbox.variable_list.del_button_mode = True

class EventMatchingBox(BoxLayout):
    before_threshold = NumericProperty(-2.)
    after_threshold = NumericProperty(2.)
    ds = ObjectProperty(None)

    def set_before_threshold(self, value):
        self.before_threshold = value

    def set_after_threshold(self, value):
        self.after_threshold = value


class VariablePairer(BoxLayout):
    current_pick_1 = ObjectProperty(None)
    current_pick_2 = ObjectProperty(None)
    available_variables = ListProperty([])
    variable_panel_1 = ObjectProperty(None)
    variable_panel_2 = ObjectProperty(None)

    def __init__(self, available_variables, **kwargs):
        super(VariablePairer, self).__init__(**kwargs)
        self.available_variables = available_variables

    def on_available_variables(self, instance, value):
        self.variable_panel_1.variable_list = value
        print 'vp1', self.variable_panel_1.variable_list
        self.variable_panel_2.variable_list = value
        print 'vp2', self.variable_panel_2.variable_list

class VariablesList(GridLayout):
    variable_list = ListProperty([])
    current_buttons = ListProperty([])
    current_toggled = ListProperty([])
    current_radio_button = ObjectProperty(None)
    radio_button_mode = BooleanProperty(False)
    del_button_mode = BooleanProperty(False)

    #defines a callback to be run when a button is deleted
    remove_button_callback = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(VariablesList, self).__init__(**kwargs)
        self.size_hint_y = None
        Clock.schedule_once(self.init_button_list)

    def clear_list(self):
        for each in self.current_buttons:
            self.remove_widget(each)
        self.current_buttons = []
        self.current_toggled = []

    def init_button_list(self, dt):
        self.populate_list()

    def populate_list(self):
        self.clear_widgets()
        for each in self.variable_list:
            variable_button = ToggleButton(text = each, on_release = self.button_press)
            if self.radio_button_mode:
                variable_button.group = self
            self.add_widget(variable_button)
            self.current_buttons.append(variable_button)
        self.height = len(self.variable_list) * (self.row_default_height + self.spacing)

    def deselect_all(self):
        for b in self.current_buttons:
            b.state = 'normal'
        self.current_toggled = []

    def on_radio_button_mode(self, instance, value):
        if value:
            self.deselect_all()
            for each in self.current_buttons:
                each.group = self


    def button_press(self, button):
        if self.del_button_mode:
            self.set_state(button.text, 'normal')
            self.variable_list.remove(button.text)
            self.del_button_mode = False
            if self.remove_button_callback is not None: self.remove_button_callback(button.text)
        elif button.state == 'down':
            if self.radio_button_mode:
                self.current_toggled = [button]
            else:
                self.current_toggled.append(button)
        elif button.state == 'normal':
            self.current_toggled.remove(button)


    def on_variable_list(self, instance, value):
        self.clear_list()
        self.canvas.clear()
        self.populate_list()

    def set_state(self, label, state):
        assert state in ['down', 'normal'], "State must be either 'down' or 'normal'"
        for b in self.current_buttons:
            if b.text == label:
                b.state = state
                if state == 'down' and b not in self.current_toggled: 
                    if self.radio_button_mode:
                        self.current_toggled = [b]
                    else:
                        self.current_toggled.append(b)
                if state == 'normal' and b in self.current_toggled: self.current_toggled.remove(b)

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


class LoadSave(Widget):
    ok = BooleanProperty(False)
    text = StringProperty("")
    loadfile = ObjectProperty(None)
    savefile = ObjectProperty(None)
    text_input = ObjectProperty(None)

    def __init__(self, action=None, callback=None, **kwargs):
        super(LoadSave, self).__init__(**kwargs)
        self.callback = callback
        if action == 'load':
            self.show_load()

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
        self.callback(os.path.join(path, filename[0]))
        self.dismiss_popup()

    def save(self, path, filename):
        self.callback(os.path.join(path, filename[0]))
        self.dismiss_popup()

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    filechooser = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(LoadDialog, self).__init__(**kwargs)
        # for now just default to user's home directory. In the future, we may want to
        # add some code to go to the same directory the user was in last time.
        self.filechooser.filters = ['*.csv']
        self.filechooser.path = os.path.dirname(os.path.realpath(__file__))


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)
    filechooser = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SaveDialog, self).__init__(**kwargs)
        # for now just default to user's home directory. In the future, we may want to
        # add some code to go to the same directory the user was in last time.
        self.filechooser.path = os.path.dirname(os.path.realpath(__file__))



Factory.register('LoadSave', cls=LoadSave)
Factory.register('LoadDialog', cls=LoadDialog)
Factory.register('SaveDialog', cls=SaveDialog)

if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainView())