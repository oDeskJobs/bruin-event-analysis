import kivy
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, BooleanProperty, ListProperty, StringProperty, ObjectProperty
from kivy.graphics import Line, Color, PushMatrix, PopMatrix, Translate, InstructionGroup, Rectangle, Rotate
from kivy.uix.scatter import Scatter
from kivy.lang import Builder
from kivy.uix.label import Label

def drange(start, stop, step):
    r = start
    while r < stop:
        yield r
        r += step


class Series(Widget):
    fill_color = ListProperty([1,1,1])
    highlight_color = ListProperty([1,1,0])
    enabled = BooleanProperty(False)
    data = ListProperty([])
    tick_width = NumericProperty(5)
    tick_height = NumericProperty(32)
    marker = StringProperty('tick')
    highlight_regions = ListProperty([])

    def __init__(self, plot, **kwargs):
        kwargs['size_hint'] = (None, None)
        self.plot = plot
        super(Series, self).__init__(**kwargs)
        
        self.highlights = InstructionGroup()
        self.highlights_translate = Translate()
        self.canvas.add(self.highlights)

        self.series = InstructionGroup()
        self.series_translate = Translate()
        self.canvas.add(self.series)

        self.pos = self.plot.pos
        self.size = self.plot.size
        self.plot.bind(size = self._set_size)
        self.plot.bind(pos = self._set_pos)
        self.plot.bind(viewport = self.draw)


    def enable(self):
        if self.enabled:
            return
        self.enabled = True
        self.plot.add_widget(self)

    def disable(self):
        if not self.enabled:
            return
        self.enabled = False
        self.plot.remove_widget(self)

    def resize_plot_from_data(self):
        self.plot.viewport = self.data_extents
        print self.data_extents
        self.draw()

    def on_data(self, instance, value):
        if value is None or len(value) == 0: return

        self.data_x = zip(*value)[0]
        self.data_y = zip(*value)[1]
        self.data_extents = (min(self.data_x), min(self.data_y), max(self.data_x), max(self.data_y))
        self.draw()

    def on_highlight_regions(self, instance, value):
        print "redrawing with regions", self.highlight_regions
        self.draw()

    def draw(self, *largs):
        self.series.clear()
        self.series.add(PushMatrix())
        self.series.add(Color(*self.fill_color, mode='rgb'))
        self.series.add(self.series_translate)

        tick_half_height_px = .5*self.tick_height / self.plot.vp_height_convert

        for t in self.data:
            bar_x = int(t[0])
            if bar_x >= self.plot.viewport[2]: continue
            bar_min_y = t[1] - tick_half_height_px
            bar_max_y = t[1] + tick_half_height_px

            display_pos = [int(v) for v in self.plot.to_display_point(bar_x, bar_min_y)]
            display_size = [int(v) for v in (self.tick_width, self.plot.to_display_point(bar_x, bar_max_y)[1] - display_pos[1])]
            
            if self.marker == 'tick':
                self.series.add(Rectangle(pos = display_pos, size = display_size))
            elif self.marker == 'plus':
                self.series.add(Rectangle(pos = display_pos, size = display_size))
                crossbar_pos = [display_pos[0] - 0.5*(self.tick_height-self.tick_width), display_pos[1] + 0.5*(self.tick_height-self.tick_width)]
                crossbar_size = (self.tick_height, self.tick_width)
                self.series.add(Rectangle(pos = crossbar_pos, size = crossbar_size))

        self.series.add(PopMatrix())

        # now draw the highlights, if there are any
        self.highlights.clear()
        self.highlights.add(PushMatrix())
        self.highlights.add(Color(*self.highlight_color, mode='rgb'))
        self.highlights.add(self.highlights_translate)

        highlight_height = int(1.2 * self.tick_height)

        for highlight_range in self.highlight_regions:
            start, end = highlight_range
            assert self.data_extents[1] == self.data_extents[3], "Highlights only work with x_only data."
            y_center = self.data_extents[1]
            begin_point = [int(v) for v in self.plot.to_display_point(start, y_center)]
            end_point = [int(v) for v in self.plot.to_display_point(end, y_center)]

            self.highlights.add(Rectangle(pos = (begin_point[0], begin_point[1] - highlight_height/2) , size = (end_point[0] - begin_point[0], highlight_height)))

        self.highlights.add(PopMatrix())



    def _set_pos(self, instance, value):
        print 'setting pos', value
        self.pos = value

    def _set_size(self, instance, value):
        print 'setting size', value
        self.size = value

    def on_pos(self, instance, value):
        self.series_translate.xy = self.x, self.y
        self.highlights_translate.xy = self.x, self.y

    def on_size(self, instance, value):
        self.draw()

    def get_legend_icon(self, size=32, **kwargs):
        # returns a kivy Image widget that matches the tick mark used in self.draw, for use in legends etc
        ic = Widget(size_hint = (None, None), size = (size,size))
        with ic.canvas:
            Color(1,1,1, mode='rgb')
            Rectangle(pos=ic.pos, size=ic.size)

class Plot(Widget):
    viewport = ListProperty([0,0,100,10])
    border_width = NumericProperty(5)
    border_color = ListProperty([.3,.3,.3])
    tick_distance_x = NumericProperty(10)
    tick_distance_y = NumericProperty(1)
    tick_color = ListProperty([.3,.3,.3])
    left_margin = NumericProperty(25)
    bottom_margin = NumericProperty(25)
    right_margin = NumericProperty(0)
    top_margin = NumericProperty(0)
    x_axis_title = StringProperty(None) 
    y_axis_title = StringProperty(None)
    text_color = ListProperty([0,0,0])

    def __init__(self, **kwargs):
        
        # these can easily be refactored to all use the same translate
        self.ticks = InstructionGroup()
        self.tick_translate = Translate()

        self.border = InstructionGroup()
        self.border_translate = Translate()

        self.x_axis_label = InstructionGroup()
        self.x_axis_label_translate = Translate()

        self.y_axis_label = InstructionGroup()
        self.y_axis_label_translate = Translate()

        
        super(Plot, self).__init__(**kwargs)
        self.canvas.add(self.ticks)
        self.canvas.add(self.border)
        self.canvas.add(self.x_axis_label)
        self.canvas.add(self.y_axis_label)


    # recalculate viewport when size changes
    def on_size(self, instance, value):
        self.on_viewport(None, self.viewport)

    def on_pos(self, instance, value):
        self.tick_translate.xy = self.x, self.y
        self.border_translate.xy = self.x, self.y
        self.x_axis_label_translate.xy = self.x, self.y
        self.y_axis_label_translate.xy = self.x, self.y
        
    def on_viewport(self, instance, value):
        if value is None or len(value) != 4: return
        self.vp_width_convert = (float(self.width)-self.left_margin-self.right_margin)/(value[2] - value[0])
        self.vp_height_convert = (float(self.height)-self.bottom_margin-self.top_margin)/(value[3] - value[1])
        self.draw_ticks()
        self.draw_border()
        self.draw_axis_labels()

    def draw_ticks(self):
        self.ticks.clear()
        self.ticks.add(PushMatrix())
        self.ticks.add(Color(*self.tick_color, mode='rgb'))
        self.ticks.add(self.tick_translate)
        if self.tick_distance_x is not None:
            first_x_tick = self.tick_distance_x*(int(self.viewport[0]/self.tick_distance_x) + 1)
            for x in drange(first_x_tick, self.viewport[2], self.tick_distance_x):
                start = self.to_display_point(x, self.viewport[1])
                stop = self.to_display_point(x, self.viewport[3])
                self.ticks.add(Line(points=[start[0], start[1], stop[0], stop[1]]))

        if self.tick_distance_y is not None:
            first_y_tick = self.tick_distance_y*(int(self.viewport[1]/self.tick_distance_y) + 1)
            for y in drange(first_y_tick, self.viewport[3], self.tick_distance_y):
                start = self.to_display_point(self.viewport[0], y)
                stop = self.to_display_point(self.viewport[2], y)
                self.ticks.add(Line(points=[start[0], start[1], stop[0], stop[1]]))
        
        self.ticks.add(PopMatrix())

    def draw_border(self):
        print "drawing border, pos is", self.pos, "bottom margin is ", self.bottom_margin
        self.border.clear()
        self.border.add(PushMatrix())
        self.border.add(Color(*self.border_color, mode='rgb'))
        self.border.add(self.border_translate)
        if self.border_width != 0:
            self.border.add(Line(rectangle = (self.left_margin, self.bottom_margin, self.width-self.left_margin-self.right_margin, self.height-self.bottom_margin-self.top_margin), width=self.border_width, joint='miter'))
        self.border.add(PopMatrix())

    def draw_axis_labels(self):
        self.x_axis_label.clear()
        self.x_axis_label.add(PushMatrix())
        self.border.add(Color(*self.text_color, mode='rgb'))
        self.x_axis_label.add(self.x_axis_label_translate)
        if self.x_axis_title_texture is not None:
            self.x_axis_label.add(
                        Rectangle(pos = (.5*self.width - .5*self.x_axis_title_texture.size[0], 0), 
                            size = self.x_axis_title_texture.size,
                            texture=self.x_axis_title_texture))
        self.x_axis_label.add(PopMatrix())

        self.y_axis_label.clear()
        self.y_axis_label.add(PushMatrix())
        self.border.add(Color(*self.text_color, mode='rgb'))

        self.y_axis_label.add(self.y_axis_label_translate)

        


        if self.y_axis_title_texture is not None:
            w,h = self.y_axis_title_texture.size

            t = Translate()
            t.xy = (.5*h, .5*self.height)
            self.y_axis_label.add(t)

            rot = Rotate()
            rot.angle = 90
            self.y_axis_label.add(rot)

            self.y_axis_label.add(
                        Rectangle(pos =  (-w*.5, -h*.5),
                            size = (w,h),
                            texture = self.y_axis_title_texture,
                            ))

        
        
        self.y_axis_label.add(PopMatrix())


    def on_y_axis_title(self, instance, value):
        if value is None:
            self.y_axis_title_texture = None
            return
        l = Label(text = value)
        l.texture_update()
        self.y_axis_title_texture = l.texture

    def on_x_axis_title(self, instance, value):
        if value is None: 
            self.x_axis_title_texture = None
            return
        l = Label(text = value)
        l.texture_update()
        self.x_axis_title_texture = l.texture



    def to_display_point(self, x, y):
        return (self.left_margin + self.vp_width_convert*(x-self.viewport[0]), self.bottom_margin + self.vp_height_convert*(y-self.viewport[1]))

class PlotExplorer(Widget):
    plot_container = ObjectProperty(None)
    annotations = ListProperty([])

    def __init__(self, plot_widget, annotations_dict, **kwargs):
        super(PlotExplorer, self).__init__(**kwargs)
        self.plot_widget = plot_widget
        self.annotations_dict = annotations_dict
        self.plot_container.add_widget(self.plot_widget)
        self.plot_container.bind(pos=self._reposition_plot)

    def on_touch_down(self, touch):
        if self.plot_widget.collide_point(*touch.pos):
            self.display_annotation(self.plot_widget.select_point(*touch.pos))

    def on_touch_move(self, touch):
        if self.plot_widget.collide_point(*touch.pos):
            self.display_annotation(self.plot_widget.select_point(*touch.pos))

    def _reposition_plot(self, instance, pos):
        self.plot_widget.pos = pos

    def display_annotation(self, data_point):
        try:
            self.annotations = self.annotations_dict[data_point[0]]
        except KeyError:
            self.annotations = []
