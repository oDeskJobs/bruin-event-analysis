from kivy_plotter.plot import Series
from kivy.properties import ListProperty
from kivy.uix.widget import Widget



class SeriesController(Widget):

    series_dict = {}
    tick_height = 20
    tick_width = 5
    all_variables_list = ListProperty([])

    def __init__(self, visualizer):
        self.visualizer = visualizer
        self.color_palette = ColorPalette()


    def add_data(self, label, xy_data, marker = 'tick'):
        # if label is new, make a new series
        if label not in self.series_dict.keys():
            s = Series(self.visualizer, fill_color = self.color_palette.get_color(label), marker = marker, tick_height = self.tick_height, tick_width = self.tick_width)
            self.series_dict[label] = s

        t = self.series_dict[label]
        if t.data is None: t.data = []
        t.data = t.data + xy_data
        if label not in self.all_variables_list and len(t.data) > 0: self.all_variables_list.append(label)
        # print self.all_variables_list
        print "Adding %s data points to series '%s'; series now contains %s items." % (len(xy_data), label, len(t.data))


    def clear(self, label = None, except_label = None):
        # use clear(label=name) to clear a given column, or use clear(except_label=name) to remove all columns *except* a given column
        if label is not None:
            if label in self.series_dict: self.series_dict[label].data = []
            if label in self.all_variables_list: self.all_variables_list.remove(label)
        elif except_label is not None:
            for each in self.all_variables_list:
                if each != except_label:
                    self.series_dict[each].data = []
            self.all_variables_list = [except_label] if except_label in self.all_variables_list else []

    def update_visible_series(self, list_of_labels):
        for label in self.series_dict.keys():
            if label in list_of_labels:
                self.enable(label)
            else:
                self.disable(label)
        if len(list_of_labels) > 0:
            self.fit_to_all_series()

    def enable(self, label):
        self.series_dict[label].enable()

    def disable(self, label):
        self.series_dict[label].disable()

    def fit_to_all_series(self):
        all_extents = [None, None, None, None]
        for k, v in self.series_dict.iteritems():
            if v.enabled:
                if all_extents[0] is None or v.data_extents[0] < all_extents[0]:  all_extents[0] = v.data_extents[0]
                if all_extents[1] is None or v.data_extents[1] < all_extents[1]:  all_extents[1] = v.data_extents[1]
                if all_extents[2] is None or v.data_extents[2] > all_extents[2]:  all_extents[2] = v.data_extents[2]
                if all_extents[3] is None or v.data_extents[3] > all_extents[3]:  all_extents[3] = v.data_extents[3]
        if None not in all_extents:
            x_range = all_extents[2] - all_extents[0]
            y_range = all_extents[3] - all_extents[1]
            self.visualizer.viewport = [all_extents[0] - 0.1*x_range, all_extents[1] - 0.1*y_range,
                                        all_extents[2] + 0.1*x_range, all_extents[3] + 0.1*y_range]

 
class ColorPalette(object):
    colors = [
    (.68, .42, .73),
    (.13, .24, .62),
    (1, 0, 0),
    (0, 1, 0),
    (0, 0, 1)
    ]

    color_dict = {}
    next_color_up = 0

    def get_and_assign_color(self, label):
        c = self.colors[self.next_color_up]
        self.next_color_up = (self.next_color_up + 1) % len(self.colors)
        self.color_dict[label] = c
        return c

    def get_color(self, label):
        try:
            return self.color_dict[label]
        except KeyError:
            return self.get_and_assign_color(label)
