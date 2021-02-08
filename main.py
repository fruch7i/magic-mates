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
import numpy as np

# the number of cols (and also rows) of the PlayingField
cols = 7

# a dictionary with all abilities, used to init the Ability class
# key: base name *** 0: manacost *** 1: target_type *** 2: reach *** 3: time_usage
ability_dict = {'move': [0, 'move', 'axe', 'half'],
        'knights move': [20, 'move', 'knight', 'half'],
        'teleport': [50, 'move', 'infinite', 'full'],
        'summon ghost': [100, 'summon', 'infinite', 'full'],
        'pass': [0, 'none', 'none', 'half'],
        'attack': [0, 'enemy', 'weapon', 'full'],
        'rookie charge': [20, 'all', 'rook', 'full'],
        'bishop charge': [20, 'all', 'bishop', 'full'],
        'mana strike': [0, 'enemy', 'weapon', 'full'],
        'quick attack': [10, 'enemy', 'weapon', 'half'],
        'knights attack': [20, 'enemy', 'knight', 'full'],
        'freeze': [30, 'enemy', 'infinite', 'full'],
        'electrocute': [30, 'enemy', 'infinite', 'full'],
        'burn': [30, 'enemy', 'infinite', 'full'],
        'manaburn': [30, 'enemy', 'infinite', 'full'],
        'poison': [30, 'enemy', 'infinite', 'full'],
        'invigorate': [40, 'ally', 'infinite', 'full'],
        'stun': [40, 'enemy', 'infinite', 'full']}

# ToDo, add:
# weapon differences:
# sword and shield: range: +1, +col, damage reduction from front (50%) and side (25%)
# axe: range: +1, +col, +1+col
# axe and buckler: lower damage output, damage reduction from front (20%) and side (10%)
# spear: range: +1, +2, +col, +2col, +1+col
# bow: range: till obstacle, maybe like queen only
# magic staff: range: infinite
# wand and buckler: range infinite, deals very little damage, grants damage reduction from front (20%) and side (10%)

# flanking bonus damage:
# bonus damage if allies are on opposing sides

# new abilities:
# double attack
# heal
# regenerate
# mana gift
# morale boost: time increase
# cleanse: defensive removal of buffs
# purge: offensive removal of buffs
# shield bash: attack + push back
# shield raise: damage reduction increase
# magic shield: blocking next buff application
# powershot: bow attack + push back
# piercing shot: bow attack + bow attack to target behind
# stab back: spear attack + push back
# axe pull: swap places with target + backstab attack
# swirl: axe attack to all targets available
# rookie charge: rook movement + attack
# novices thunder: very weak attack spell with insane gains through level up

# abilities level up:
# freeze: stun on apply, infinite time, ally targeting freeze blade
# burn: stronger burn, infinite time, ally targeting burn blade
# double attack: triple attack
# heal: heal all
# regenerate: regenerate all

# inkscape images of wizards
# wizards with different weapons
# load images based on weapon
# team 1: black drawing on white background
# team 2: white drawing on black background

# a dictionary with the connection between abilities and their respective applied buffs
buff_dict = {'freeze': 'frozen',
        'burn': 'burning',
        'manaburn': 'manaburning',
        'poison': 'poisoned',
        'invigorate': 'invigorated',
        'stun': 'stunned'}

# a dictionary mapping weapon to its base_damage
weapon_dict = {'longsword': 30,
        'sword and shield': 20,
        'axe': 30,
        'axe and buckler': 20,
        'spear': 20,
        'bow': 20,
        'magic staff': 10,
        'wand and buckler': 5}

class Ability():
    def __init__(self, name):
        self.base = name
        self.upgrades = [name]
        self.possible_upgrades = ['test1', 'test2', 'test3']
        self.manacost = ability_dict[name][0]
        self.target_type = ability_dict[name][1]
        self.reach = ability_dict[name][2]
        self.time_usage = ability_dict[name][3]
        self.experience = 0
        self.lvl_up_experience = 10
        self.level = 1

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

    team = NumericProperty(0)
    weapon = StringProperty('')
    base_damage = 0

    def __init__(self, team, abilities, weapon, **kwargs):
        super().__init__(**kwargs)
        self.health = self.max_health
        self.mana = self.max_mana
        self.t = random.randint(0,99)
        self.team = team
        self.abilities = abilities
        self.weapon = weapon
        self.base_damage = weapon_dict[weapon]

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

    def attack(self, target, damage):
        ''' attacking a target Mate '''
        for child in self.children:
            try:
                if child.mode == 'invigorated':
                    damage = child.stacks * damage
                    self.remove_buff(child)
            except AttributeError:
                pass
        for child in self.children:
            try:
                if child.mode == 'freeze blade' or child.mode == 'burn blade' or child.mode == 'manaburn blade':
                    target.create_buff(child.ability)
            except AttributeError:
                pass
        target.change_health(damage, 0)

    def ma_on_release(self):
        self.show_details_popup()

    def show_details_popup(self):
        ''' open an InfoPopup that shows all the details about the character '''
        popup = InfoPopup(self)
        popup.open()

    def create_buff(self, ability):
        ''' add a new buff to the Mate '''
        buff_found = False
        for child in self.children:
            if type(child) is Buff:
                if child.mode == buff_dict[ability.base]:
                    child.apply_buff(self)
                    buff_found = True
        if buff_found == False:
            self.add_widget(Buff(ability, self))

    def remove_buff(self, buff):
        ''' remove a buff from the Mate '''
        self.remove_widget(buff)

    def create_select_button(self, source, ability):
        ''' create a SelectButton on this Mate, so that it can be selected as a target by other Mates '''
        self.add_widget(SelectButton(source, ability))

    def create_select_buttons(self, ability):
        ''' create select buttons based on the ability used '''
        index = self.parent.children[:].index(self)
        if ability.reach == 'weapon':
            reach = self.weapon
        else:
            reach = ability.reach

        if reach == 'longsword' or reach == 'sword and shield':
            index_list = [index+1, index-1, index+cols, index-cols]
            index_list = [i for i in index_list if i >= 0 and i < cols**2] # remove upper and lower borders
            try:
                if index%cols == 0: # remvoe left border
                    index_list.remove(index-1)
                if index%cols == 9: # remove right border
                    index_list.remove(index+1)
            except ValueError:
                pass

        elif reach == 'axe':
            index_list = [index+1, index-1, index+cols, index-cols, index+1+cols, index-1+cols, index+1-cols, index-1-cols]
            index_list = [i for i in index_list if i >= 0 and i < cols**2] # remove upper and lower borders
            if index%cols == 0:
                index_list = [i for i in index_list if i%cols <= 2] # remove right border
            if index%cols == cols-1:
                index_list = [i for i in index_list if i%cols >= cols-3] # remove left border

        elif reach == 'spear':
            index_list = [index+1, index-1, index+2, index-2, index+cols, index-cols, index+2*cols, index-2*cols, index+1+cols, index-1+cols, index+1-cols, index-1-cols]
            index_list = [i for i in index_list if i >= 0 and i < cols**2] # remove upper and lower borders
            if index%cols == 0 or index%cols == 1:
                index_list = [i for i in index_list if i%cols <= 3] # remove right border
            if index%cols == cols-1 or index%cols == cols-2:
                index_list = [i for i in index_list if i%cols >= cols-4] # remove left border

        elif reach == 'knight':
            index_list = [index+cols+2, index+cols-2, index+2*cols+1, index+2*cols-1, index-cols+2, index-cols-2, index-2*cols+1, index-2*cols-1]
            index_list = [i for i in index_list if i >= 0 and i < cols**2] # remove upper and lower borders
            if index%cols == 0 or index%cols == 1:
                index_list = [i for i in index_list if i%cols <= 3] # remove right border
            if index%cols == cols-1 or index%cols == cols-2:
                index_list = [i for i in index_list if i%cols >= cols-4] # remove left border

        elif reach == 'rook':
            index_list = []
            for i in range(1, cols+2): # going top
                if index+i*cols >= cols**2:
                    break
                if type(self.parent.children[index+i*cols]) is Mate:
                    break
                index_list.append(index+i*cols)

            for i in range(1, cols+2): # going bottom
                if index-i*cols < 0:
                    break
                if type(self.parent.children[index-i*cols]) is Mate:
                    break
                index_list.append(index-i*cols)

            for i in range(1, cols+2): # going right
                if index%cols == 0:
                    break
                if type(self.parent.children[index-i]) is Mate:
                    break
                index_list.append(index-i)
                if (index-i)%cols == 0:
                    break

            for i in range(1, cols+2): # going left
                if index%cols == cols-1:
                    break
                if type(self.parent.children[index+i]) is Mate:
                    break
                index_list.append(index+i)
                if (index+i)%cols == cols-1:
                    break

        elif reach == 'bishop':
            index_list = []
            top_right = True
            top_left = True
            bot_right = True
            bot_left = True
            for i in range(1, cols+2):
                if top_right:
                    if index%cols == 0 or index >= cols**2-cols:
                        top_right = False
                    if top_right:
                        if type(self.parent.children[index-i+i*cols]) is Mate:
                            top_right = False
                        else:
                            index_list.append(index-i+i*cols)
                            if (index-i+i*cols)%cols == 0 or (index-i+i*cols) >= cols**2-cols:
                                top_right = False
                if top_left:
                    if index%cols == cols-1 or index >= cols**2-cols:
                        top_left = False
                    if top_left:
                        if type(self.parent.children[index+i+i*cols]) is Mate:
                            top_left = False
                        else:
                            index_list.append(index+i+i*cols)
                            if (index+i+i*cols)%cols == cols-1 or (index+i+i*cols) >= cols**2-cols:
                                top_left = False
                if bot_right:
                    if index%cols == 0 or index < cols:
                        bot_right = False
                    if bot_right:
                        if type(self.parent.children[index-i-i*cols]) is Mate:
                            bot_right = False
                        else:
                            index_list.append(index-i-i*cols)
                            if (index-i-i*cols)%cols == 0 or (index-i-i*cols) <= cols:
                                bot_right = False
                if bot_left:
                    if index%cols == cols-1 or index < cols:
                        bot_left = False
                    if bot_left:
                        if type(self.parent.children[index+i-i*cols]) is Mate:
                            bot_left = False
                        else:
                            index_list.append(index+i-i*cols)
                            if (index+i-i*cols)%cols == cols-1 or (index+i-i*cols) <= cols:
                                bot_left = False

        elif reach == 'infinite' or reach == 'magic staff' or reach == 'wand and buckler':
            index_list = list(range(0, cols**2))
            index_list.remove(index)

        elif reach == 'none':
            index_list = [index]

        # create SelectButtons based on weather the abilities targeting type is move, enemy, ally or all mates
        for i in index_list:
            child = self.parent.children[i]
            if ability.target_type == 'move' or ability.target_type == 'summon':
                if type(child) is EmptyField:
                    child.create_select_button(self, ability)
            if ability.target_type == 'none':
                self.end_ability(ability, self)
            if ability.target_type == 'enemy':
                if type(child) is Mate:
                    if self.team != child.team:
                        child.create_select_button(self, ability)
            if ability.target_type == 'ally':
                if type(child) is Mate:
                    if self.team == child.team:
                        child.create_select_button(self, ability)
            if ability.target_type == 'all':
                child.create_select_button(self, ability)

    def start_ability(self, ability):
        ''' initiate the target selection '''
        self.create_select_buttons(ability)

    def end_ability(self, ability, target):
        ''' end the ability selection, performing the ability here '''
        self.change_mana(ability.manacost, 0)
        ability.experience += 1
        if ability.experience >= ability.lvl_up_experience:
            ability.level += 1
            ability.experience = 0
        if ability.target_type == 'move':
            self.parent.switch_positions_by_ref(self, target)
        elif ability.base == 'rookie charge' or ability.base == 'bishop charge':
            self.parent.switch_positions_by_ref(self, target)
        elif ability.base == 'pass':
            self.change_health(0, 10)
            self.change_mana(0, 10)
        elif ability.base == 'summon ghost':
            self.parent.create_ghost(self.team, target)
        elif ability.base == 'attack' or ability == 'knights attack':
            self.attack(target, self.base_damage)
        elif ability.base == 'mana strike':
            damage = (1. + 0.02 * self.mana) * self.base_damage
            self.attack(target, damage)
            self.mana = 0.0
        elif ability.base == 'quick attack':
            self.attack(target, 0.5*self.base_damage)
        elif ability.base == 'electrocute':
            self.attack(target, 2.*self.base_damage)
            target.t += 0.5 * (target.max_t - target.t)
        else:
            target.create_buff(ability)
        self.end_turn(ability)

    def start_turn(self):
        ''' start the turn by setting game.is_running to False, adding ability prompts '''
        # ToDo: add sufficient mana check here, grey out unavailable ability prompts
        game = App.get_running_app().root
        menu = game.ids['ability_menu']
        for ability in self.abilities:
            menu.create_ability_prompt(self, ability)

    def end_turn(self, ability):
        ''' end the turn by resetting t and game.is_running, and removing all AbilityPrompts '''
        if ability.time_usage == 'full':
            self.t = 0.
        elif ability.time_usage == 'half':
            self.t = 0.5 * self.max_t
        else:
            print('Error, ability.time_usage not valid')
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
            if self.t >= self.max_t:
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
    ''' a Popup showing some information about the Mate '''
    team_label = StringProperty()
    health_label = StringProperty()
    mana_label = StringProperty()
    time_label = StringProperty()
    weapon_label = StringProperty()
    buff_label = StringProperty()
    abilities_label = StringProperty()
    def __init__(self, mate, **kwargs):
        super().__init__(**kwargs)
        self.team_label = "team: {}".format(mate.team)
        self.health_label = "health: {0:0.1f}/{1:0.1f} regenerating {2:0.2f}".format(mate.health, mate.max_health, mate.health_regen)
        self.mana_label = "mana: {0:0.1f}/{1:0.1f} regenerating {2:0.2f}".format(mate.mana, mate.max_mana, mate.mana_regen)
        self.time_label = "time: {0:0.1f}/{1:0.1f}".format(mate.t, mate.max_t)
        self.weapon_label = "weapon {0} with base damage: {1:0.1f}".format(mate.weapon, mate.base_damage)
        self.abilities_label = "active Abilities: \n"
        for ability in mate.abilities:
            self.abilities_label += ability.base + ' ( lvl: ' + str(ability.level) + ' / exp: ' + str(ability.experience) + ')' + '\n'
        self.buff_label = "active Buffs: \n"
        for child in mate.children:
            if type(child) is Buff:
                self.buff_label += child.mode + '(' + str(child.stacks) + ') remaining time: ' + str(child.t) + '\n'

class Buff(Widget):
    ''' a widget used to save permanent and temporary changes (buffs/debuffs) on a Mate '''
    t = 0.
    stacks = 0
    def __init__(self, ability, target, **kwargs):
        super().__init__(**kwargs)
        self.ability = ability
        self.mode = buff_dict[ability.base]
        self.apply_buff(ability, target)

    def apply_buff(self, ability, target):
        self.stacks += 1
        self.t += 200.
        if ability.base == 'freeze':
            target.t = 0.5 * target.t
            target.max_t += 10
        if ability.base == 'manaburn':
            target.change_mana(40, 0)
        if ability.base == 'stun':
            self.t = np.infty

    def remove_buff(self):
        if self.mode == 'frozen':
            mem_t = self.parent.t / self.parent.max_t
            self.parent.max_t -= self.stacks * 10
            self.parent.t = mem_t * self.parent.max_t
        self.parent.remove_buff(self)

    def update(self, *args):
        game = App.get_running_app().root
        if game.is_running:
            self.t -= 1
            if self.mode == 'poisoned':
                self.parent.change_health(0, -2.*self.parent.health_regen)
            if self.mode == 'burning':
                self.parent.change_health(self.stacks*0.02, 0)
            if self.mode == 'manaburning':
                self.parent.change_health(0, -self.stacks*self.parent.mana_regen)
            if self.mode == 'stunned':
                self.parent.t -= 2.
                if self.parent.t < 0:
                    self.remove_buff()
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
        if source.mana < ability.manacost:
            button.disabled = True

class AbilityPrompt(RelativeLayout):
    name = StringProperty('')
    def __init__(self, source, ability, **kwargs):
        super().__init__(**kwargs)
        self.ability = ability
        self.name = ability.base
        self.source = source
    def ap_on_release(self):
        self.source.start_ability(self.ability)

class PlayingField(GridLayout):
    ''' the playing field where MagicMates move around '''
    t = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = cols
        for i in range(0, self.cols**2):
            self.add_widget(EmptyField())
        self.create_mate(1, [Ability('move'), Ability('bishop charge'), Ability('pass')], 'axe', 2)
        self.create_mate(1, [Ability('move'), Ability('bishop charge'), Ability('pass')], 'longsword', 3)
        self.create_mate(1, [Ability('move'), Ability('attack'), Ability('manaburn')], 'wand and buckler', 4)

        self.create_mate(2, [Ability('move'), Ability('attack'), Ability('poison')], 'spear', 44)
        self.create_mate(2, [Ability('move'), Ability('attack'), Ability('invigorate')], 'axe', 45)
        self.create_mate(2, [Ability('move'), Ability('attack'), Ability('mana strike')], 'magic staff', 46)

    def switch_positions(self, index1, index2):
        ''' switch positions of two children '''
        self.children[index1], self.children[index2] = self.children[index2], self.children[index1]

    def switch_positions_by_ref(self, object1, object2):
        ''' switch positions of two children without knowing the indices of the objects '''
        self.switch_positions(self.children[:].index(object1), self.children[:].index(object2))

    def create_mate(self, team, abilities, weapon, index):
        ''' create a new Mate by adding it to the children list, swapping it with the according EmptyField, finally removing the EmptyField '''
        self.add_widget(Mate(team, abilities, weapon))
        self.switch_positions(index+1, 0)
        self.remove_widget(self.children[0])

    def create_ghost(self, team, target):
        ''' create a new Mate with lower stats '''
        ghost = Mate(team, ['move', 'attack', 'pass'], 'axe')
        ghost.max_health = 50
        ghost.base_damage = 15
        ghost.t = 1.
        self.add_widget(ghost)
        index = self.children[:].index(target)
        self.switch_positions(index, 0)
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

