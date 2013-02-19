from kivy_plotter.plot import Series


class SeriesController(object):

    series_dict = {}
    tick_height = 20
    tick_width = 5

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

    def enable(self, label):
        self.series_dict[label].enable()
        self.fit_to_all_series()

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

    def __init__(self):
        self.color_generator = (c for c in self.colors)

    def get_and_assign_color(self, label):
        c = self.color_generator.next()
        self.color_dict[label] = c
        return c

    def get_color(self, label):
        try:
            return self.color_dict[label]
        except KeyError:
            return self.get_and_assign_color(label)
