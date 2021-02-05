from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.properties import ObjectProperty, NumericProperty, BoundedNumericProperty, StringProperty

import random

class Mate(FloatLayout):
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

    def change_health(self, damage, heal):
        self.health = self.health - damage + heal
        if self.health < 0.:
            self.die()
        if self.health > self.max_health:
            self.health = self.max_health

    def change_mana(self, manacost, managain):
        self.mana = self.mana - manacost + managain
        if self.mana < 0:
            self.mana = 0
        if self.mana > self.max_mana:
            self.mana = self.max_mana

    def ma_on_release(self):
        self.create_buff('test')

    def create_buff(self, mode):
        self.add_widget(Buff(mode))

    def remove_buff(self, buff):
        self.remove_widget(buff)

    def create_select_button(self, source, ability):
        self.add_widget(SelectButton(source, ability))

    def create_select_buttons(self, ability):
        ''' create select buttons based on the ability used '''
        index = self.parent.children[:].index(self)

        if  ability == 'move' or ability == 'attack':
            reach = 'direct'
        elif ability == 'knightsmove':
            reach = 'knight'
        else:
            reach = 'infinite'

        if reach == 'direct':
            index_list = [index+1, index-1, index+10, index-10]
            index_list = [i for i in index_list if i >= 0 and i < 100] # remove upper and lower borders
            try:
                if index%10 == 0: # remvoe left border
                    index_list.remove(index-1)
                if index%10 == 9: # remove right border
                    index_list.remove(index+1)
            except ValueError:
                pass

        elif reach == 'knight':
            index_list = [index+12, index-12, index+8, index-8, index+21, index-21, index+19, index-19]
            if index < 20: # remove bottom border
                try:
                    index_list.remove(index-19)
                except ValueError:
                    pass
                try:
                    index_list.remove(index-21)
                except ValueError:
                    pass
            if index < 10:
                try:
                    index_list.remove(index-8)
                except ValueError:
                    pass
                try:
                    index_list.remove(index-12)
                except ValueError:
                    pass
            if index >= 80: # remove top border
                try:
                    index_list.remove(index+19)
                except ValueError:
                    pass
                try:
                    index_list.remove(index+21)
                except ValueError:
                    pass
            if index >= 90:
                try:
                    index_list.remove(index+8)
                except ValueError:
                    pass
                try:
                    index_list.remove(index+12)
                except ValueError:
                    pass

            if index%10 <= 1: # remove right border
                try:
                    index_list.remove(index+8)
                except ValueError:
                    pass
                try:
                    index_list.remove(index-12)
                except ValueError:
                    pass
            if index%10 == 0: 
                try:
                    index_list.remove(index+19)
                except ValueError:
                    pass
                try:
                    index_list.remove(index-21)
                except ValueError:
                    pass
            if index%10 >= 8: # remove left border
                try:
                    index_list.remove(index-8)
                except ValueError:
                    pass
                try:
                    index_list.remove(index+12)
                except ValueError:
                    pass
            if index%10 == 9: 
                try:
                    index_list.remove(index-19)
                except ValueError:
                    pass
                try:
                    index_list.remove(index+21)
                except ValueError:
                    pass

        elif reach == 'infinite':
            index_list = range(0, 100)

        for i in index_list:
            child = self.parent.children[i]
            if ability == 'move' or ability == 'knightsmove' and type(child) is EmptyField:
                child.create_select_button(self, ability)
            if ability == 'attack' and type(child) is Mate:
                child.create_select_button(self, ability)

    def start_ability(self, ability):
        ''' initiate the target selection '''
        self.create_select_buttons(ability)

    def end_ability(self, ability, target):
        ''' end the ability selection, performing the ability here '''
        if ability == 'move' or ability == 'knightsmove':
            self.parent.switch_positions_by_ref(self, target)
        elif ability == 'attack':
            target.change_health(50, 0)
        self.end_turn()
        print('index after moving: {}'.format(self.parent.children.index(self)))

    def start_turn(self):
        ''' start the turn by setting game.is_running to False, adding ability prompts '''
        # ToDo: add sufficient mana check here, grey out unavailable ability prompts
        game = App.get_running_app().root
        menu = game.ids['ability_menu']
        menu.create_ability_prompt(self, 'move')
        menu.create_ability_prompt(self, 'attack')
        menu.create_ability_prompt(self, 'knightsmove')
        menu.create_ability_prompt(self, 'test2')

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
            self.change_health(0, self.health_regen)
            self.change_mana(0, self.mana_regen)
            self.t += 1.
            if self.t > self.max_t:
                game.is_running = False
                self.start_turn()
        for child in self.children:
            try:
                child.update(*args)
            except AttributeError:
                pass

    def die(self):
        ''' called when the mate dies '''
        self.parent.remove_mate(self)

class Buff(Widget):
    ''' a widget used to save permanent and temporary changes (buffs/debuffs) on a Mate '''
    t = 100.
    stacks = 1
    def __init__(self, mode, **kwargs):
        super().__init__(**kwargs)
        self.mode = mode

    def remove_buff(self):
        self.parent.remove_buff(self)

    def update(self, *args):
        game = App.get_running_app().root
        if game.is_running:
            self.t -= 1
            if self.t < 0.:
                self.remove_buff()

class SelectButton(Button):
    ''' a button to select a target, either an EmptyField or a Mate '''
    def __init__(self, source, ability, **kwargs):
        super().__init__(**kwargs)
        self.source = source
        self.ability = ability

    def sb_on_release(self):
        self.source.end_ability(self.ability, self.parent)

class EmptyField(RelativeLayout):
    ''' an empty field in the playing field '''
    def ef_on_release(self):
        print('EmptyField.ef_on_release called')

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
    def create_ability_prompt(self, source, ability):
        self.add_widget(AbilityPrompt(source, ability))

class AbilityPrompt(RelativeLayout):
    ability = StringProperty('')
    def __init__(self, source, ability, **kwargs):
        super().__init__(**kwargs)
        self.ability = ability
        self.source = source
    def ap_on_release(self):
        self.source.start_ability(self.ability)

class PlayingField(GridLayout):
    ''' the playing field where MagicMates move around '''
    t = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 10
        for i in range(0, self.cols**2):
            self.add_widget(EmptyField())
        self.create_mate(1)
        self.create_mate(11)
        self.create_mate(12)

    def switch_positions(self, index1, index2):
        ''' switch positions of two children '''
        self.children[index1], self.children[index2] = self.children[index2], self.children[index1]

    def switch_positions_by_ref(self, object1, object2):
        ''' switch positions of two children without knowing the indices of the objects '''
        self.switch_positions(self.children[:].index(object1), self.children[:].index(object2))

    def create_mate(self, index):
        ''' create a new Mate by adding it to the children list, swapping it with the according EmptyField, finally removing the EmptyField '''
        self.add_widget(Mate())
        self.switch_positions(index+1, 0)
        self.remove_widget(self.children[0])

    def remove_mate(self, mate):
        ''' remove a Mate by adding an EmptyField, switching it in, and removing the Mate '''
        empty_field = EmptyField()
        self.add_widget(empty_field)
        self.switch_positions_by_ref(empty_field, mate)
        self.remove_widget(mate)

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

