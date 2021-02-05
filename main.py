from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty, NumericProperty, BoundedNumericProperty, StringProperty

import random

# a dictionary with all abilities, their manacost, their targeting type and reach
ability_dict = {'move': [0, 'move', 'direct'],
        'knightsmove': [20, 'move', 'knight'],
        'teleport': [50, 'move', 'infinite'],
        'attack': [0, 'enemy', 'direct'],
        'knights attack': [0, 'enemy', 'knight'],
        'freeze': [30, 'enemy', 'infinite']}

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

    team = NumericProperty(0)

    def __init__(self, team, **kwargs):
        super().__init__(**kwargs)
        self.health = self.max_health
        self.mana = self.max_mana
        self.t = random.randint(0,99)
        self.team = team

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
        self.show_details_popup()

    def show_details_popup(self):
        ''' open an InfoPopup that shows all the details about the character '''
        popup = InfoPopup(self)
        popup.open()

    def create_buff(self, mode):
        ''' add a new buff to the Mate '''
        buff_found = False
        for child in self.children:
            if type(child) is Buff:
                if child.mode == mode:
                    child.apply_buff(self)
                    buff_found = True
        if buff_found == False:
            self.add_widget(Buff(mode, self))

    def remove_buff(self, buff):
        ''' remove a buff from the Mate '''
        self.remove_widget(buff)

    def create_select_button(self, source, ability):
        ''' create a SelectButton on this Mate, so that it can be selected as a target by other Mates '''
        self.add_widget(SelectButton(source, ability))

    def create_select_buttons(self, ability):
        ''' create select buttons based on the ability used '''
        index = self.parent.children[:].index(self)

        if ability_dict[ability][2] == 'direct':
            index_list = [index+1, index-1, index+10, index-10]
            index_list = [i for i in index_list if i >= 0 and i < 100] # remove upper and lower borders
            try:
                if index%10 == 0: # remvoe left border
                    index_list.remove(index-1)
                if index%10 == 9: # remove right border
                    index_list.remove(index+1)
            except ValueError:
                pass

        elif ability_dict[ability][2] == 'knight':
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

        elif ability_dict[ability][2] == 'infinite':
            index_list = list(range(0, 100))
            index_list.remove(index)

        # create SelectButtons based on weather the abilities targeting type is move, enemy, friend or all mates
        for i in index_list:
            child = self.parent.children[i]
            if ability_dict[ability][1] == 'move':
                if type(child) is EmptyField:
                    child.create_select_button(self, ability)
            if ability_dict[ability][1] == 'enemy':
                if type(child) is Mate:
                    if self.team != child.team:
                        child.create_select_button(self, ability)

    def start_ability(self, ability):
        ''' initiate the target selection '''
        self.create_select_buttons(ability)

    def end_ability(self, ability, target):
        ''' end the ability selection, performing the ability here '''
        self.change_mana(ability_dict[ability][0], 0)
        if ability_dict[ability][1] == 'move':
            self.parent.switch_positions_by_ref(self, target)
        elif ability == 'attack':
            target.change_health(50, 0)
        elif ability == 'freeze':
            target.create_buff(ability)
        self.end_turn()

    def start_turn(self):
        ''' start the turn by setting game.is_running to False, adding ability prompts '''
        # ToDo: add sufficient mana check here, grey out unavailable ability prompts
        game = App.get_running_app().root
        menu = game.ids['ability_menu']
        for key in ability_dict:
            menu.create_ability_prompt(self, key)

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

class InfoPopup(Popup):
    team_label = StringProperty()
    health_label = StringProperty()
    mana_label = StringProperty()
    time_label = StringProperty()
    dmg_label = StringProperty()
    buff_label = StringProperty()
    abil_label = StringProperty()
    def __init__(self, mate, **kwargs):
        super().__init__(**kwargs)
        self.team_label = "team: {}".format(mate.team)
        self.health_label = "health: {0:0.1f}/{1:0.1f} regenerating {2:0.2f}".format(mate.health, mate.max_health, mate.health_regen)
        self.mana_label = "mana: {0:0.1f}/{1:0.1f} regenerating {2:0.2f}".format(mate.mana, mate.max_mana, mate.mana_regen)
        self.time_label = "time: {0:0.1f}/{1:0.1f}".format(mate.t, mate.max_t)
        self.dmg_label = "base damage: {0:0.1f}".format(mate.base_dmg)
        self.buff_label = "active Buffs: \n"
        for child in mate.children:
            if type(child) is Buff:
                self.buff_label += child.mode + '(' + str(child.stacks) + ') remaining time: ' + str(child.t) + '\n'

class Buff(Widget):
    ''' a widget used to save permanent and temporary changes (buffs/debuffs) on a Mate '''
    t = 0.
    stacks = 0
    def __init__(self, mode, target, **kwargs):
        super().__init__(**kwargs)
        self.mode = mode
        self.apply_buff(target)

    def apply_buff(self, target):
        self.stacks += 1
        self.t += 200.
        if self.mode == 'freeze':
            target.t = 0.5 * target.t
            target.max_t += 10

    def remove_buff(self):
        if self.mode == 'freeze':
            mem_t = self.parent.t / self.parent.max_t
            self.parent.max_t -= self.stacks * 10
            self.parent.t = mem_t * self.parent.max_t
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
        button = AbilityPrompt(source, ability)
        self.add_widget(button)
        if source.mana < ability_dict[ability][0]:
            button.disabled = True

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
        self.create_mate(1, 14)
        self.create_mate(1, 15)
        self.create_mate(1, 16)
        self.create_mate(2, 24)
        self.create_mate(2, 25)
        self.create_mate(2, 26)

    def switch_positions(self, index1, index2):
        ''' switch positions of two children '''
        self.children[index1], self.children[index2] = self.children[index2], self.children[index1]

    def switch_positions_by_ref(self, object1, object2):
        ''' switch positions of two children without knowing the indices of the objects '''
        self.switch_positions(self.children[:].index(object1), self.children[:].index(object2))

    def create_mate(self, team, index):
        ''' create a new Mate by adding it to the children list, swapping it with the according EmptyField, finally removing the EmptyField '''
        self.add_widget(Mate(team))
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

