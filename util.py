from kivy_plotter.plot import Series, ArrowList
from kivy.properties import ListProperty, DictProperty
from kivy.uix.widget import Widget



class SeriesController(Widget):

    series_dict = {}
    tick_height = 20
    tick_width = 5
    all_variables_list = ListProperty([])
    x_only_fields = []
    arrows = DictProperty({})

    # determines where on the y_axis series show up if they don't have y data
    x_only_field_y_hints = [[],
                            [.75], 
                            [.6, .8], 
                            [.4, .6, .8], 
                            [.2, .4, .6, .8], 
                            [.1, .3, .5, .7, .9],
                            ]

    def __init__(self, visualizer):
        self.visualizer = visualizer
        self.visualizer.bind(viewport = self.viewport_changed)
        self.color_palette = ColorPalette()

    def add_data(self, label, xy_data, marker = 'tick', is_x_only = False):
        if len(xy_data) == 0: return
        # if label is new, make a new series
        if label not in self.series_dict.keys():
            s = Series(self.visualizer, fill_color = self.color_palette.get_color(label), marker = marker, tick_height = self.tick_height, tick_width = self.tick_width)
            self.series_dict[label] = s
            if is_x_only and label not in self.x_only_fields: self.x_only_fields.append(label)
        t = self.series_dict[label]
        if t.data is None: t.data = []
        if is_x_only: 
            t.data = t.data + self.reshape_x_only_data(label, xy_data)
        else:
            t.data = t.data + xy_data
        if label not in self.all_variables_list and len(t.data) > 0: self.all_variables_list.append(label)
        # print self.all_variables_list
        print "Adding %s data points to series '%s'; series now contains %s items." % (len(xy_data), label, len(t.data))

    def reshape_x_only_data(self, label, xy_data):
        enabled_x_only_fields = [l for l in self.x_only_fields if self.series_dict[l].enabled or l == label]
        if len(enabled_x_only_fields) == 0: enabled_x_only_fields = self.x_only_fields
        all_y_hints = self.x_only_field_y_hints[len(enabled_x_only_fields)]
        series_y_hint = all_y_hints[enabled_x_only_fields.index(label)]
        series_y = self.visualizer.viewport[1] + series_y_hint*(self.visualizer.viewport[3] - self.visualizer.viewport[1])
        print [(t[0], series_y) for t in xy_data]
        return [(t[0], series_y) for t in xy_data]


    def viewport_changed(self, instance, value):
        self.reassign_y_values_to_x_only_series()


    def reassign_y_values_to_x_only_series(self):
        for label in self.x_only_fields:
            t = self.series_dict[label]
            if not t.data: continue
            t.data = self.reshape_x_only_data(label, t.data)

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
        if label in self.x_only_fields: self.reassign_y_values_to_x_only_series()

    def disable(self, label):
        self.series_dict[label].disable()
        if label in self.x_only_fields: self.reassign_y_values_to_x_only_series()

    def get_data(self, label):
        return self.series_dict[label].data

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
            if x_range <= 0: x_range = 1
            if y_range <= 0: y_range = 1
            self.visualizer.viewport = [all_extents[0] - 0.1*x_range, all_extents[1] - 0.1*y_range,
                                        all_extents[2] + 0.1*x_range, all_extents[3] + 0.1*y_range]

    def add_highlights(self, label, regions):
        self.series_dict[label].highlight_regions = regions

    def add_arrows(self, start_label, end_label, x_ranges):
        if (start_label, end_label) not in self.arrows:
            self.arrows[(start_label, end_label)] = ArrowList(self.series_dict[start_label], self.series_dict[end_label], x_ranges)        
        else:
            self.arrows[(start_label, end_label)].x_ranges = x_ranges

        self.arrows[(start_label, end_label)].enable()

    def clear_arrows(self):
        for _, v in self.arrows.iteritems():
            v.disable()


    # def enable_arrows(self, start_label, end_label):
    #     self.arrows[(start_label, end_label)].enable()

    # def disable_arrows(self, start_label, end_label):
    #     self.arrows[(start_label, end_label)].disable()    


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
