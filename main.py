from kivy.uix.listview import ListView
from kivy.uix.widget import Widget
from kivy.lang import Builder

Builder.load_file('ui.kv')

class MainView(Widget):
    pass

class ListBox(Widget):
    pass

if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainView())