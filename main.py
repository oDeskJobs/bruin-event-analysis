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
from kivy.config import Config

from double_slider import DoubleSlider
from data_models import TransientDataFile, BehaviorDataFile
from util import SeriesController, Workspace, Subject, Session

import os
from functools import partial

Builder.load_file('ui.kv')
Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '700')



def get_bout_regions_from_xy_data(data, bout_threshold = 1., single_events_are_bouts = True):
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
        elif single_events_are_bouts and not in_bout and not within_threshold:
            if len(bouts) == 0 or x1[0] not in bouts[-1]: bouts.append((x1[0], x1[0]))

        # if x2 == sorted_data[-1]:
        x1 = x2

    # special logic for last event
    if in_bout:
        bouts.append((current_bout_start, x2[0]))
    elif single_events_are_bouts:
        bouts.append((x2[0], x2[0]))



    return bouts

def get_transitions_from_xy_data_obselete(data1, data2, threshold = 1.):
    data_dict = {k[0]: 1 for k in data1}
    _data_dict2 = {k[0]:2 if k not in data1 else 3 for k in data2}
    data_dict.update(_data_dict2)
    all_keys = sorted(data_dict.keys())
    
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

def get_transitions_from_xy_data(data1, data2, threshold = 1.):
    data_dict = {k[0]: 1 for k in data1}
    _data_dict2 = {k[0]: 2 if k not in data1 else 3 for k in data2}
    data_dict.update(_data_dict2)
    all_keys = sorted(data_dict.keys())
    print data_dict
    print all_keys
    
    cursor_in_data1 = False
    cursor_not_in_data1_until = 0
    transitions = []

    for x2 in all_keys:
        if data_dict[x2] != 1:
            if cursor_in_data1 and x2 - threshold <= x1:
                transitions.append((x1,x2))
            cursor_in_data1 = False
        elif data_dict[x2] == 1:
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
    schema = StringProperty(None, allownone = True)
    transient_schema = StringProperty(None, allownone = True)
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
        self.transient_button_list.remove_button_callback = self._remove_transient_callback
        self.transient_button_list.bind(current_toggled=self._transient_select_changed)

        self.behavior_button_list = self.behavior_box.listbox.variable_list
        self.behavior_button_list.remove_button_callback = self._remove_behavior_callback
        self.behavior_button_list.bind(current_toggled=self._behavior_select_changed)

        self.legend_button_list = self.legend_box.listbox.variable_list
        self.legend_button_list.bind(current_toggled=self._visible_series_changed)

        self.bout_id_button_list = self.bout_id_box.listbox.variable_list
        self.bout_id_button_list.bind(current_toggled=self._bout_id_params_changed)
        self.bout_id_box.bind(bout_threshold=self._bout_id_params_changed)
        self.bout_id_box.bind(single_events_are_bouts=self._bout_id_params_changed)
        self.bout_id_box.export_callback = self.bout_id_export

        self.transition_button_list = self.transition_box.listbox.variable_list
        self.transition_button_list.bind(current_toggled=self._transition_params_changed)
        self.transition_box.bind(transition_threshold=self._transition_params_changed)
        self.transition_box.export_callback = self.transition_export

        self.event_button_list = self.event_box.listbox.variable_list
        self.event_button_list.bind(current_toggled=self._event_params_changed)
        self.event_box.bind(before_threshold=self._event_params_changed)
        self.event_box.bind(after_threshold=self._event_params_changed)
        self.event_box.export_callback = self.event_export

        self.filechooser_path = os.path.dirname(os.path.realpath(__file__))
        
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
            show_message("You must choose a subject before importing files.")
            return
        LoadSave(action='load', callback=self._add_transient_file, filters=['*.csv'], path = self.filechooser_path)

    def prompt_for_behavior_file(self):
        if self.current_subject is None: 
            show_message("You must choose a subject before importing files.")
            return
        if self.schema is None:
            show_message("You must choose a schema before importing a behavior file.")
            return
        LoadSave(action='load', callback=self._add_behavior_file, filters=['*.csv'], path = self.filechooser_path)

    def prompt_for_schema(self):
        if self.current_subject is None: 
            show_message("You must choose a subject before importing files.")
            return
        LoadSave(action='load', callback=self._add_schema, filters=['*.schema'], path = self.filechooser_path)

    def prompt_for_transient_schema(self):
        if self.current_subject is None: 
            show_message("You must choose a subject before importing files.")
            return
        LoadSave(action='load', callback=self._add_transient_schema, filters=['*.schema'], path = self.filechooser_path)

    def _add_transient_file(self, directory, name):
        self.filechooser_path = directory
        path = os.path.join(directory, name)
        
        if self.transient_schema is None or not os.path.isfile(self.transient_schema):
            print "No schema file present. Aborting."
            return
        
        try:
            t = TransientDataFile(path, self.transient_schema)
        except:
            show_message("Could not import this file as a transient data file. Aborting.")
            return

        if os.path.basename(t.source_file) in [os.path.basename(x.source_file) for x in self.transient_files]:
            show_message("This file has already been imported for this subject. Aborting.")
            return

        self.transient_files.append(t)
        self.transient_button_list.set_state(os.path.basename(t.source_file), 'down')

    def on_transient_files(self, instance, value):
        self.transient_button_list.variable_list = [os.path.basename(t.source_file) for t in self.transient_files]

    def on_behavior_files(self, instance, value):
        self.behavior_button_list.variable_list = [os.path.basename(t.source_file) for t in self.behavior_files]

    def on_sessions(self, instance, value):
        self.session_button_list.variable_list = [str(x) for x in self.sessions]

    def on_subjects(self, instance, value):
        self.subject_button_list.variable_list = [str(x) for x in self.subjects]

    def _transient_select_changed(self, instance, value):
        print "transient select changed"
        selected_basenames = [v.text for v in value]
        self.series_controller.clear(label = 'Transients')
        self.series_controller.clear_files(transient=True)
        for t in self.transient_files:
            if os.path.basename(t.source_file) in selected_basenames:
                data = [p for p in t.get_xy_pairs()]
                self.series_controller.add_data('Transients', data)
                self.series_controller.add_file(t, transient=True)

    def _behavior_select_changed(self, instance, value):
        selected_basenames = [v.text for v in value]
        self.series_controller.clear(except_label = 'Transients')
        self.series_controller.clear_files()
        for s in self.behavior_files:
            if os.path.basename(s.source_file) in selected_basenames:
                for field in s.get_valid_time_columns():
                    data = [p for p in s.get_xy_pairs(x=field)]
                    self.series_controller.add_data(field, data, marker='plus', is_x_only = True)
                self.series_controller.add_file(s)

    def _add_behavior_file(self, directory, name):
        self.filechooser_path = directory
        path = os.path.join(directory, name)
        
        if self.schema is None or not os.path.isfile(self.schema):
            print "No schema file present. Aborting."
            return

        try:
            t = BehaviorDataFile(path, self.schema)
        except:
            show_message("Could not import this file as a behavior data file. Aborting.")
            return

        if os.path.basename(t.source_file) in [os.path.basename(x.source_file) for x in self.behavior_files]:
            show_message("This file has already been imported for this subject. Aborting.")
            return

        self.behavior_files.append(t)
        self.behavior_button_list.set_state(os.path.basename(t.source_file), 'down')
        

    def _all_variables_changed(self, instance, value):
        self.bout_id_box.listbox.variable_list.variable_list = [v for v in sorted(value, key=self.label_sort_func) if v != "Transients" and not v.startswith("Bouts:")]
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
        # self.series_controller.clear(startswith = 'Bouts:')
        for t in self.bout_id_box.listbox.variable_list.current_toggled:
            label = t.text
            data = self.series_controller.get_data(label)
            bouts = get_bout_regions_from_xy_data(data, bout_threshold = self.bout_id_box.bout_threshold, 
                    single_events_are_bouts = self.bout_id_box.single_event_checkbox.active)
            # add bout data to series controller for event matching
            self.series_controller.add_data("Bouts: " + label, [(b[0], None) for b in bouts], marker='plus', is_x_only = True, replace_previous_data = True)
            self.series_controller.add_highlights(t.text, bouts)

    def calculate_transitions(self, *largs):
        self.series_controller.clear_arrows()
        for t in self.transition_box.listbox.variable_list.current_toggled:
            # split label into two variables using "->" as delimiter
            label1, label2 = [v.strip() for v in t.text.split('->')]
            data1, data2 = [self.series_controller.get_data(l) for l in (label1, label2)]
            transitions = get_transitions_from_xy_data(data1, data2, threshold = self.transition_box.transition_threshold)
            self.series_controller.add_arrows(label1, label2, transitions)
            # add transition data to series controller for event matching
            self.series_controller.add_data("Transition: " + label1 + " -> " + label2, [(t[0], None) for t in transitions], marker='plus', is_x_only = True, replace_previous_data = True)
            

    def calculate_event_matches(self, *largs):
        self.series_controller.clear_col_highlights()
        for t in self.event_box.listbox.variable_list.current_toggled:
            label = t.text
            before_dist = self.event_box.before_threshold
            after_dist = self.event_box.after_threshold
            self.series_controller.add_col_highlights(label, -before_dist, after_dist)

    def add_subject(self):
        if self.current_session is None:
            show_message("Please select a session before adding a subject.")
            return
        p = AskForTextPopup(title = "New Subject", label= "Please name this subject.", callback = self._add_subject_callback)
        p.open()

    def add_session(self):
        p = AskForTextPopup(title = "New Session", label= "Please name this session.", callback = self._add_session_callback)
        p.open()

    def _add_session_callback(self, session_name):
        if session_name.strip() == "": return
        if len([s for s in self.sessions if s.name == session_name]) != 0:
            show_message("That name is already used; please choose a different one.")
            return
        s = Session(session_name)
        self.sessions.append(s)
        self.session_button_list.set_state(session_name, 'down')

    def _add_subject_callback(self, subject_name):
        if subject_name.strip() == "" or self.current_session is None: return
        if len([s for s in self.subjects if s.name == subject_name]) != 0:
            show_message("That name is already used; please choose a different one.")
            return
        self.current_session.add_subject(subject_name)
        self.subjects = self.current_session.subjects
        self.subject_button_list.set_state(subject_name, 'down')

    def remove_behavior_button(self):
        self.behavior_button_list.del_button_mode = not self.behavior_button_list.del_button_mode

    def remove_transient_button(self):
        self.transient_button_list.del_button_mode = not self.transient_button_list.del_button_mode

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
        self.session_button_list.del_button_mode = not self.session_button_list.del_button_mode

    def remove_subject_button(self):
        self.subject_button_list.del_button_mode = not self.subject_button_list.del_button_mode

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

    def _remove_transient_callback(self, text):
        self.transient_files = [t for t in self.transient_files if os.path.basename(t.source_file) != text]

    def _remove_behavior_callback(self, text):
        self.behavior_files = [t for t in self.behavior_files if os.path.basename(t.source_file) != text]

    def _add_schema(self, directory, name):
        self.filechooser_path = directory
        filename = os.path.join(directory, name)
        if not os.path.isfile(filename) or not filename.endswith('.schema'): 
            show_message("Sorry, this is not a valid schema file.")
            return
        self.schema = filename

    def _add_transient_schema(self, directory, name):
        self.filechooser_path = directory
        filename = os.path.join(directory, name)
        if not os.path.isfile(filename) or not filename.endswith('.schema'): 
            show_message("Sorry, this is not a valid schema file.")
            return
        self.transient_schema = filename

    def on_schema(self, instance, value):
        if value is None:
            self.behavior_box.schema_button.text = "Load Schema..."
            self.behavior_box.schema_button.state = 'normal'
        else:
            self.behavior_box.schema_button.text = "Schema loaded."
            self.behavior_box.schema_button.state = 'down'

    def on_transient_schema(self, instance, value):
        if value is None:
            self.transient_box.schema_button.text = "Load Schema..."
            self.transient_box.schema_button.state = 'normal'
        else:
            self.transient_box.schema_button.text = "Schema loaded."
            self.transient_box.schema_button.state = 'down'

    def bout_id_export(self, series_labels):
        #TODO add better checks here
        if len(series_labels) == 0: 
            show_message("No variables selected for export.")
            return
        LoadSave(action='save', callback=partial(self._bout_id_export_callback, series_labels), filters=['*.csv'], path = self.filechooser_path)

    def transition_export(self, series_labels):
        #TODO add better checks here
        if len(series_labels) == 0: 
            show_message("No variables selected for export.")
            return
        LoadSave(action='save', callback=partial(self._transition_export_callback, series_labels), filters=['*.csv'], path = self.filechooser_path)

    def event_export(self, series_labels):
        if len(series_labels) == 0: 
            show_message("No variables selected for export.")
            return
        elif 'Transients' not in self.series_controller.all_variables_list:
            show_message("Please import transient data before running event matching.")
            return
        LoadSave(action='save', callback=partial(self._event_export_callback, series_labels), filters=['*.csv'], path = self.filechooser_path)
        

    def _bout_id_export_callback(self, series_labels, out_filepath, out_filename):
        self.filechooser_path = out_filepath
        outfile = os.path.join(out_filepath, out_filename)
        outf_basename = os.path.splitext(outfile)[0]
        for label in series_labels:
            suffix = ''.join([c for c in label if c.isalnum()])
            self.series_controller.export_bouts(label, outf_basename+'_'+suffix+'.csv')

    def _transition_export_callback(self, series_labels, out_filepath, out_filename):
        self.filechooser_path = out_filepath
        outfile = os.path.join(out_filepath, out_filename)
        outf_basename = os.path.splitext(outfile)[0]
        for label in series_labels:
            suffix = ''.join([c for c in label if c.isalnum()])
            self.series_controller.export_transitions(label, outf_basename+'_'+suffix+'.csv')

    def _event_export_callback(self, series_labels, out_filepath, out_filename):
        self.filechooser_path = out_filepath        
        outfile = os.path.join(out_filepath, out_filename)

        outf_basename = os.path.splitext(outfile)[0]
        for label in series_labels:
            suffix = ''.join([c for c in label if c.isalnum()])
            self.series_controller.export_events(label, outf_basename+'_'+suffix+'.csv')

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
    export_callback = ObjectProperty(None)
    single_event_checkbox = ObjectProperty(None)
    single_events_are_bouts = BooleanProperty(True)

    def toggle_checkbox(self):
        self.single_event_checkbox.active = not self.single_event_checkbox.active
        self.single_events_are_bouts = self.single_event_checkbox.active

    def set_threshold(self, value):
        self.bout_threshold = value

    def export_data(self):
        selected = [v.text for v in self.listbox.variable_list.current_toggled]
        if self.export_callback is not None:
            self.export_callback(selected)

    def get_manual_input(self):
        request_input("Please choose a value", self.accept_manual_input)

    def accept_manual_input(self, value):
        try:
            floatval = float(value.strip())
            self.slider.value = floatval
        except Exception as e:
            print e
            show_message("Not a valid input")

class TransitionIDBox(BoxLayout):
    transition_threshold = NumericProperty(1.)
    available_variables = ListProperty([])
    variable_pairs = ListProperty([])
    listbox = ObjectProperty(None)
    slider = ObjectProperty(None)

    def set_threshold(self, value):
        self.transition_threshold = value

    def add_variable_pair(self):
        variable_pairer = VariablePairer([v for v in self.available_variables if not v.startswith('Transition:')])
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
        self.listbox.variable_list.del_button_mode = not self.listbox.variable_list.del_button_mode

    def export_data(self):
        selected = [v.text for v in self.listbox.variable_list.current_toggled]
        if self.export_callback is not None:
            self.export_callback(selected)

    def get_manual_input(self):
        request_input("Please choose a value", self.accept_manual_input)

    def accept_manual_input(self, value):
        try:
            floatval = float(value.strip())
            self.slider.value = floatval
        except Exception as e:
            print e
            show_message("Not a valid input")


class EventMatchingBox(BoxLayout):
    before_threshold = NumericProperty(-2.)
    after_threshold = NumericProperty(2.)
    ds = ObjectProperty(None)

    def set_before_threshold(self, value):
        self.before_threshold = value

    def set_after_threshold(self, value):
        self.after_threshold = value
    
    def export_data(self):
        selected = [v.text for v in self.listbox.variable_list.current_toggled]
        if self.export_callback is not None:
            self.export_callback(selected)

    def get_manual_input1(self):
        request_input("Please choose a value", self.accept_manual_input1)

    def accept_manual_input1(self, value):
        try:
            floatval = float(value.strip())
            self.ds.value = floatval
        except Exception as e:
            print e
            show_message("Not a valid input")

    def get_manual_input2(self):
        request_input("Please choose a value", self.accept_manual_input2)

    def accept_manual_input2(self, value):
        try:
            floatval = float(value.strip())
            self.ds.value2 = floatval
        except Exception as e:
            print e
            show_message("Not a valid input")

class BehaviorBox(BoxLayout):
    load_schema_callback = ObjectProperty(None)
    add_button_callback = ObjectProperty(None)
    remove_button_callback = ObjectProperty(None)
    schema_button = ObjectProperty(None)

class TransientBox(BoxLayout):
    # This REALLY ought to be refactored into the same class as BehaviorBox. Pretty embarrassing.
    load_schema_callback = ObjectProperty(None)
    add_button_callback = ObjectProperty(None)
    remove_button_callback = ObjectProperty(None)
    schema_button = ObjectProperty(None)

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

    def populate_list(self, toggled_text = None):
        if toggled_text is None: toggled_text = []
        self.canvas.clear()
        self.clear_widgets()
        for each in self.variable_list:
            variable_button = ToggleButton(text = each, on_release = self.button_press)
            if self.radio_button_mode:
                variable_button.group = self
            self.add_widget(variable_button)
            self.current_buttons.append(variable_button)
        self.height = len(self.variable_list) * (self.row_default_height + self.spacing)

        for label in toggled_text:
            self.set_state(label, 'down')

    def deselect_all(self):
        for b in self.current_buttons:
            b.state = 'normal'
        self.current_toggled = []

    def on_radio_button_mode(self, instance, value):
        if value:
            self.deselect_all()
            for each in self.current_buttons:
                each.group = self

    def on_del_button_mode(self, instance, value):
        if value:
            for each in self.current_buttons:
                each.background_color = [1, 0, 0, 1]
        else:
            for each in self.current_buttons:
                each.background_color = [1, 1, 1, 1]

    def button_press(self, button):
        if self.del_button_mode:
            self.set_state(button.text, 'normal')
            self.variable_list.remove(button.text)
            self.del_button_mode = False
            if self.remove_button_callback is not None: self.remove_button_callback(button.text)
        elif button.state == 'down':
            if self.radio_button_mode:
                self.current_radio_button = button
                self.current_toggled = [button]
            else:
                self.current_toggled.append(button)
        elif button.state == 'normal':
            self.current_toggled.remove(button)


    def on_variable_list(self, instance, value):
        toggled_text = [v.text for v in self.current_toggled]
        self.clear_list()
        self.del_button_mode = False
        self.populate_list(toggled_text = toggled_text)

    def set_state(self, label, state):
        assert state in ['down', 'normal'], "State must be either 'down' or 'normal'"
        
        # this should not be necessary, but it is.
        if state == 'down' and self.radio_button_mode: self.deselect_all()

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


def show_message(text):
    popup = MessagePopup(text=text)
    popup.open()

class MessagePopup(Popup):

    def __init__(self, text = "", **kwargs):

        kwargs['size_hint'] = (None, None)
        kwargs['size'] = (300, 200)
        kwargs['title'] = "Message"
        kwargs['content'] = MessagePopupContent(text = text, ok_callback = self._ok_callback)

        super(MessagePopup, self).__init__(**kwargs)

    def _ok_callback(self):
        self.dismiss()

class MessagePopupContent(Widget):
    ok_callback = ObjectProperty(None)
    text = StringProperty("")

def request_input(prompt, callback):
    popup = PromptPopup(prompt, callback)
    popup.open()

class PromptPopup(Popup):

    def __init__(self, prompt, callback, **kwargs):
        self.callback = callback
        kwargs['size_hint'] = (None, None)
        kwargs['size'] = (300, 200)
        kwargs['title'] = "User Input"
        kwargs['content'] = PromptPopupContent(prompt = prompt, ok_callback = self._ok_callback)

        super(PromptPopup, self).__init__(**kwargs)

    def _ok_callback(self, *args, **kwargs):
        self.callback(*args, **kwargs)
        self.dismiss()

class PromptPopupContent(Widget):
    ok_callback = ObjectProperty(None)
    prompt = StringProperty("")
    value = StringProperty("")

class LoadSave(Widget):
    ok = BooleanProperty(False)
    text = StringProperty("")
    loadfile = ObjectProperty(None)
    savefile = ObjectProperty(None)
    text_input = ObjectProperty(None)
    filters = ListProperty(None)

    def __init__(self, action=None, callback=None, path = None, **kwargs):
        super(LoadSave, self).__init__(**kwargs)
        self.callback = callback
        self.filechooser_path = path if path is not None else os.path.dirname(os.path.realpath(__file__))
        if action == 'load':
            self.show_load()
        elif action == 'save':
            self.show_save()


    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(filters = self.filters, load=self.load, cancel=self.dismiss_popup, path = self.filechooser_path)
        self._popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def show_save(self):
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup, path = self.filechooser_path)
        self._popup = Popup(title="Save file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        self.callback(path, filename[0])
        self.dismiss_popup()

    def save(self, path, filename):
        self.callback(path, filename)
        self.dismiss_popup()

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    filechooser = ObjectProperty(None)


    def __init__(self, filters = None, path = None, **kwargs):
        super(LoadDialog, self).__init__(**kwargs)
        # for now just default to user's home directory. In the future, we may want to
        # add some code to go to the same directory the user was in last time.
        self.filechooser.filters = filters
        print path
        if path is not None:
            self.filechooser.path = path


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)
    filechooser = ObjectProperty(None)

    def __init__(self, path = None, **kwargs):
        super(SaveDialog, self).__init__(**kwargs)
        # for now just default to user's home directory. In the future, we may want to
        # add some code to go to the same directory the user was in last time.
        if path is not None:
            self.filechooser.path = path

if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainView())