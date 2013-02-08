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

class LinePlot(Widget):
    """MOSTLY OBSELETE, KEEPING FOR REFERENCE"""
    viewport = ListProperty(None)
    line_width = NumericProperty(5.)
    line_color = ListProperty([0,.8,1])
    border_width = NumericProperty(5)
    border_color = ListProperty([.3,.3,.3])
    flattened_points = ListProperty(None)
    tick_distance_x = NumericProperty(None)
    tick_distance_y = NumericProperty(None)
    tick_color = ListProperty([.3,.3,.3])
    select_circle = ListProperty([0,0,0])

    def __init__(self, points, **kwargs):
        # calculate some basic information about the data
        self.points = points
        self.points_x = zip(*points)[0]
        self.points_y = zip(*points)[1]

        # if we could figure out how to draw an arbitrary number of ticks in kv, this would be cleaner
        self.ticks = InstructionGroup()
        self.tick_translate = Translate()
        

        super(LinePlot, self).__init__(**kwargs)
        self.canvas.insert(0, self.ticks)
        self.viewport = (min(self.points_x), min(self.points_y), max(self.points_x), max(self.points_y))
    
    # recalculate viewport when size changes
    def on_size(self, instance, value):
        self.on_viewport(None, self.viewport)

    def on_pos(self, instance, value):
        self.tick_translate.xy = self.x, self.y
        
    def on_viewport(self, instance, value):
        if value is None or len(value) != 4: return
        print value
        self.vp_width_convert = float(self.width)/(value[2] - value[0])
        self.vp_height_convert = float(self.height)/(value[3] - value[1])

        # calculate the actual display points based on the viewport and self.size
        self.display_points = [self.to_display_point(*p) for p in self.points if value[0] <= p[0] <= value[2] and value[1] <= p[1] <= value[3]]
        self.flattened_points = [item for sublist in self.display_points for item in sublist]
        self.draw_ticks()

    # it would be real nice if we could figure out how to do this in kv
    def draw_ticks(self):
        self.ticks.clear()
        self.ticks.add(Color(*self.tick_color, mode='rgb'))
        self.ticks.add(PushMatrix())
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

    def to_display_point(self, x, y):
        return (self.vp_width_convert*(x-self.viewport[0]), self.vp_height_convert*(y-self.viewport[1]))

    def select_point(self, x, y):
        # get point from self.displaypoints that is closest to x
        
        distances = [abs((x - self.x) - d[0]) for d in self.display_points]
        idx = min(xrange(len(distances)),key=distances.__getitem__)
        self.select_circle = [self.display_points[idx][0], self.display_points[idx][1], 20]
        return self.points[idx]




    def to_xy(self, x, y):
        xt = (x - self.x)/self.vp_width_convert+self.viewport[0]
        yt = (y - self.y)/self.vp_height_convert+self.viewport[1]
        return (xt, yt)


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
