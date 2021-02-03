from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.clock import Clock
from kivy.properties import ObjectProperty, NumericProperty, BoundedNumericProperty, StringProperty

import random

class Mate(Button):
    ''' the base class for characters, the mages moving on the PlayingField '''
    # you have to declare the properties at class level, not at init, in order to get expected behaviour
    max_t = 100
    t = NumericProperty(0)

    max_health = 100.0
    health = NumericProperty(1.0)
    health_regen = 0.1

    max_mana = 100.0
    mana = NumericProperty(1.0)
    mana_regen = 0.1

    base_dmg = 30

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.health = self.max_health
        self.mana = self.max_mana
        self.t = random.randint(0,99)

    def ma_on_release(self):
        pass

    def create_move_buttons(self):
        for child in self.parent.children:
            if type(child) is Mate:
                pass
            if type(child) is EmptyField:
                child.create_select_button(self, 'move')

    def move(self, target):
        self.parent.switch_positions_by_ref(self, target)
        self.end_turn()

    def start_turn(self):
        game = App.get_running_app().root
        menu = game.ids['ability_menu']
        menu.create_ability_prompt()
        menu.create_ability_prompt()
        menu.create_ability_prompt()
        self.create_move_buttons()

    def end_turn(self):
        ''' end the turn by resetting t and game.is_running, and removing all AbilityPrompts '''
        self.t = 0.
        game = App.get_running_app().root
        game.is_running = True
        menu = game.ids['ability_menu']
        for child in menu.children[:]:
            if type(child) is AbilityPrompt:
                menu.remove_widget(child)
        playing_field = game.ids['playing_field']
        for child in playing_field.children[:]:
            for grandchild in child.children[:]:
                if type(grandchild) is SelectButton:
                    child.remove_widget(grandchild)

    def update(self, *args):
        game = App.get_running_app().root
        if game.is_running:
            self.t += 1.
            if self.t > self.max_t:
                game.is_running = False
                self.start_turn()
        for child in self.children:
            try:
                child.update(*args)
            except AttributeError:
                pass

class SelectButton(Button):
    ''' a button to select a target, either an EmptyField or a Mate '''
    def __init__(self, source, ability, **kwargs):
        super().__init__(**kwargs)
        self.source = source
        self.ability = ability

    def sb_on_release(self):
        if self.ability == 'move':
            self.source.move(self.parent)

class EmptyField(RelativeLayout):
    ''' an empty field in the playing field '''
    def ef_on_release(self):
        pass

    def create_select_button(self, source, ability):
        self.add_widget(SelectButton(source, ability))

class BasicBoxLayout(BoxLayout):
    def update(self, *args):
        for child in self.children:
            try:
                child.update(*args)
            except AttributeError:
                pass

class AbilityMenu(BoxLayout):
    def create_ability_prompt(self):
        self.add_widget(AbilityPrompt('test ability'))

class AbilityPrompt(RelativeLayout):
    ability = StringProperty('init')
    def __init__(self, ability, **kwargs):
        super().__init__(**kwargs)
        self.ability = ability
    def ap_on_release(self):
        pass

class PlayingField(GridLayout):
    ''' the playing field where MagicMates move around '''
    t = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 10
        for i in range(0, self.cols**2):
            self.add_widget(EmptyField())
        self.create_mate(5)
        self.create_mate(6)

    def switch_positions(self, index1, index2):
        ''' switch positions of two children '''
        self.children[index1], self.children[index2] = self.children[index2], self.children[index1]

    def switch_positions_by_ref(self, object1, object2):
        ''' switch positions of two children without knowing the indices of the objects '''
        self.switch_positions(self.children[:].index(object1), self.children[:].index(object2))

    def create_mate(self, index):
        ''' create a new Mate by adding it to the children list, swapping it with the according EmptyField, finally removing the EmptyField '''
        self.add_widget(Mate())
        self.switch_positions(index, 0)
        self.remove_widget(self.children[0])

    def update(self, *args):
        game = App.get_running_app().root
        if game.is_running:
            self.t += 1
        for child in self.children:
            try:
                child.update(*args)
            except AttributeError:
                pass

class MagicMatesGame(BoxLayout):
    is_running = True
    def update(self, *args):
        for child in self.children:
            try:
                child.update(*args)
            except AttributeError:
                pass

class magicmatesApp(App):
    def build(self):
        game = MagicMatesGame()
        Clock.schedule_interval(game.update, 1/60.)
        return game

if __name__ == "__main__":
    magicmatesApp().run()

