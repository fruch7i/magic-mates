from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.uix.popup import Popup
from kivy.factory import Factory

game_is_running = True

class Character(Widget):
    max_health = 100
    health = 50

class ActionPrompt(Popup):

    def create(self, *args):
        global game_is_running
        game_is_running = False
        self.open()

    def close(self, *args):
        global game_is_running
        game_is_running = True
        self.dismiss()

class MaMaGame(Widget):
    t = NumericProperty(0)

    def update(self, *args):
        global game_is_running
        if game_is_running:
            self.t += 1
            if self.t % 100 == 0:
                Factory.ActionPrompt().create()

class mamaApp(App):

    def build(self):
        game = MaMaGame()
        Clock.schedule_interval(game.update, 1/60.)
        return game

if __name__ == "__main__":
    mamaApp().run()
