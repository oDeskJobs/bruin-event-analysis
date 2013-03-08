from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, AliasProperty, OptionProperty, \
        ReferenceListProperty, BoundedNumericProperty, ListProperty
from kivy.lang import Builder


Builder.load_string('''
<DoubleSlider>:
    canvas:
        Color:
            rgb: 1, 1, 1
        BorderImage:
            border: (0, 18, 0, 18) if self.orientation == 'horizontal' else (18, 0, 18, 0)
            pos: (self.x, self.center_y - 18) if self.orientation == 'horizontal' else (self.center_x - 18, self.y)
            size: (self.width, 37) if self.orientation == 'horizontal' else (37, self.height)
            source: 'atlas://data/images/defaulttheme/slider%s_background' % self.orientation[0]
        Color:
            rgb: 1, 0, 0
        BorderImage:
            border: (0, 18, 0, 18) if self.orientation == 'horizontal' else (18, 0, 18, 0)
            pos: (self.value_pos[0], self.center_y - 18) if self.orientation == 'horizontal' else (self.center_x - 18, self.y)
            size: (abs(self.get_mid_pos(self.mid)[0]-self.value_pos[0]), 37) if self.orientation == 'horizontal' else (37, self.height)
            source: 'atlas://data/images/defaulttheme/slider%s_background' % self.orientation[0]
        Color:
            rgb: 0, 1, 0
        BorderImage:
            border: (0, 18, 0, 18) if self.orientation == 'horizontal' else (18, 0, 18, 0)
            pos: (self.get_mid_pos(self.mid)[0], self.center_y - 18) if self.orientation == 'horizontal' else (self.center_x - 18, self.y)
            size: (abs(self.value2_pos[0] - self.get_mid_pos(self.mid)[0]), 37) if self.orientation == 'horizontal' else (37, self.height)
            source: 'atlas://data/images/defaulttheme/slider%s_background' % self.orientation[0]
        Color:
            rgb: 1, 1, 1
        Rectangle:
            pos: (self.value_pos[0] - 16, self.center_y - 17) if self.orientation == 'horizontal' else (self.center_x - 16, self.value_pos[1] - 16)
            size: (32, 32)
            source: 'atlas://data/images/defaulttheme/slider_cursor'
        Rectangle:
            pos: (self.value2_pos[0] - 16, self.center_y - 17) if self.orientation == 'horizontal' else (self.center_x - 16, self.value2_pos[1] - 16)
            size: (32, 32)
            source: 'atlas://data/images/defaulttheme/slider_cursor'


    ''')

def distancesq(pt1, pt2):
    return (pt2[1] - pt1[1])**2 + (pt2[0] - pt1[0])**2

class DoubleSlider(Widget):
    '''Class for creating Slider widget.

    Check module documentation for more details.
    '''

    value = NumericProperty(0.)
    value2 = NumericProperty(0.)

    min = NumericProperty(0.)
    max = NumericProperty(100.)
    mid = NumericProperty(50)
    
    padding = NumericProperty(10)
    orientation = OptionProperty('horizontal', options=(
        'vertical', 'horizontal'))

    range = ReferenceListProperty(min, max)
    step = BoundedNumericProperty(0, min=0)

    def __init__(self, **kwargs):
        super(DoubleSlider, self).__init__(**kwargs)

    def on_mid(self, instance, value):
        self.mid_pos = self.get_mid_pos(value)


    def get_norm_value(self):
        vmin = self.min
        d = self.max - vmin
        if d == 0:
            return 0
        return (self.value - vmin) / float(d)

    def get_norm_value2(self):
        vmin = self.min
        d = self.max - vmin
        if d == 0:
            return 0
        return (self.value2 - vmin) / float(d)

    def set_norm_value(self, value):
        vmin = self.min
        step = self.step
        val = value * (self.max - vmin) + vmin
        if step == 0:
            self.value = val
        else:
            self.value = min(round((val - vmin) / step) * step + vmin, self.max)


    def set_norm_value2(self, value):
        vmin = self.min
        step = self.step
        val = value * (self.max - vmin) + vmin
        if step == 0:
            self.value2 = val
        else:
            self.value2 = min(round((val - vmin) / step) * step + vmin, self.max)

    value_normalized = AliasProperty(get_norm_value, set_norm_value,
                                     bind=('value', 'min', 'max', 'step'))
    value2_normalized = AliasProperty(get_norm_value2, set_norm_value2,
                                     bind=('value2', 'min', 'max', 'step'))
    '''Normalized value inside the :data:`range` (min/max) to 0-1 range::

        >>> slider = Slider(value=50, min=0, max=100)
        >>> slider.value
        50
        >>> slider.value_normalized
        0.5
        >>> slider.value = 0
        >>> slider.value_normalized
        0
        >>> slider.value = 1
        >>> slider.value_normalized
        1

    You can also use it for setting the real value without knowing the minimum
    and maximum::

        >>> slider = Slider(min=0, max=200)
        >>> slider.value_normalized = .5
        >>> slider.value
        100
        >>> slider.value_normalized = 1.
        >>> slider.value
        200

    :data:`value_normalized` is an :class:`~kivy.properties.AliasProperty`.
    '''

    def get_mid_pos(self, mid):
        # TODO: this REALLY needs to be linked to the property, but I am pressed for time.
        # calculate mid_normalized
        vmin = self.min
        d = self.max - vmin
        if d == 0:
            mid_normalized = 0
        else:
            mid_normalized = (mid - vmin) / float(d)

        # now calculate mid_pos
        padding = self.padding
        x = self.x
        y = self.y
        nval = mid_normalized
        if self.orientation == 'horizontal':
            return (x + padding + nval * (self.width - 2 * padding), y)
        else:
            return (x, y + padding + nval * (self.height - 2 * padding))

    def get_value_pos(self):
        padding = self.padding
        x = self.x
        y = self.y
        nval = self.value_normalized
        if self.orientation == 'horizontal':
            return (x + padding + nval * (self.width - 2 * padding), y)
        else:
            return (x, y + padding + nval * (self.height - 2 * padding))

    def set_value_pos(self, pos):
        padding = self.padding
        x = min(self.right - padding, max(pos[0], self.x + padding))
        y = min(self.top - padding, max(pos[1], self.y + padding))
        if self.orientation == 'horizontal':
            if self.width == 0:
                self.value_normalized = 0
            elif x > self.get_mid_pos(self.mid)[0]: 
                x = self.get_mid_pos(self.mid)[0]
                self.value_normalized = (x - self.x - padding) / float(self.width - 2 * padding)
            else:
                self.value_normalized = (x - self.x - padding) / float(self.width - 2 * padding)
        else:
            if self.height == 0:
                self.value_normalized = 0
            else:
                self.value_normalized = (y - self.y - padding) / float(self.height - 2 * padding)
    value_pos = AliasProperty(get_value_pos, set_value_pos,
                              bind=('x', 'y', 'width', 'height', 'min',
                                    'max', 'value_normalized', 'orientation'))
    '''Position of the internal cursor, based on the normalized value.

    :data:`value_pos` is an :class:`~kivy.properties.AliasProperty`.
    '''
    def get_value2_pos(self):
        padding = self.padding
        x = self.x
        y = self.y
        nval = self.value2_normalized
        if self.orientation == 'horizontal':
            return (x + padding + nval * (self.width - 2 * padding), y)
        else:
            return (x, y + padding + nval * (self.height - 2 * padding))

    def set_value2_pos(self, pos):
        padding = self.padding
        x = min(self.right - padding, max(pos[0], self.x + padding))
        y = min(self.top - padding, max(pos[1], self.y + padding))
        if self.orientation == 'horizontal':
            if self.width == 0:
                self.value2_normalized = 0
            elif x < self.get_mid_pos(self.mid)[0]:
                x = self.get_mid_pos(self.mid)[0]
                self.value2_normalized = (x - self.x - padding) / float(self.width - 2 * padding)                
            else:
                self.value2_normalized = (x - self.x - padding) / float(self.width - 2 * padding)
        else:
            if self.height == 0:
                self.value2_normalized = 0
            else:
                self.value2_normalized = (y - self.y - padding) / float(self.height - 2 * padding)
    value2_pos = AliasProperty(get_value2_pos, set_value2_pos,
                              bind=('x', 'y', 'width', 'height', 'min',
                                    'max', 'value2_normalized', 'orientation'), cache = False)
    grabbed_slider = None

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            if self.grabbed_slider is None:
                # determine which slider is closer, and grab that one
                d1 = distancesq(self.value_pos, touch.pos)
                d2 = distancesq(self.value2_pos, touch.pos)
                if d1 < d2:
                    self.grabbed_slider = 1
                else:
                    self.grabbed_slider = 2

            if self.grabbed_slider == 1:
                self.value_pos = touch.pos
            elif self.grabbed_slider == 2:
                self.value2_pos = touch.pos
            return True

    def on_touch_move(self, touch):
        if touch.grab_current == self:
            if self.grabbed_slider == 1:
                self.value_pos = touch.pos
            elif self.grabbed_slider == 2:
                self.value2_pos = touch.pos
            return True

    def on_touch_up(self, touch):
        if touch.grab_current == self:
            if self.grabbed_slider == 1:
                self.value_pos = touch.pos
            elif self.grabbed_slider == 2:
                self.value2_pos = touch.pos
            self.grabbed_slider = None
            return True

if __name__ == '__main__':
    from kivy.app import App

    class SliderApp(App):
        def build(self):
            return DoubleSlider(min = -10, max = 10, mid = 0, value=-5, value2=5)

    SliderApp().run()
