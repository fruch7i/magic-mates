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
# target_types:
# EmptyField
# Mate
#   enemy
#   ally
# Multiple Mates:
#   all enemies
#   all allies
#   all mates
#   distinct mates

ability_dict = {'move': [0, 'move', 'axe', 'half'],
        'shield bash': [0, 'enemy', 'sword and shield', 'half'],
        'stab back': [0, 'enemy', 'spear', 'half'],
        'knights move': [20, 'move', 'knight', 'half'],
        'teleport': [50, 'move', 'infinite', 'full'],
        'summon ghost': [100, 'summon', 'infinite', 'full'],
        'pass': [0, 'none', 'none', 'half'],
        'attack': [0, 'enemy', 'weapon', 'full'],
        'axe pull': [30, 'enemy', 'weapon', 'full'],
        'rookie charge': [20, 'move', 'rook', 'full'],
        'bishop charge': [20, 'move', 'bishop', 'full'],
        'mana strike': [0, 'enemy', 'weapon', 'full'],
        'quick attack': [30, 'enemy', 'weapon', 'half'],
        'double attack': [60, 'enemy', 'weapon', 'full'],
        'knights attack': [20, 'enemy', 'knight', 'full'],
        'freeze': [30, 'enemy', 'infinite', 'full'],
        'electrocute': [30, 'enemy', 'infinite', 'full'],
        'burn': [30, 'enemy', 'infinite', 'full'],
        'manaburn': [30, 'enemy', 'infinite', 'full'],
        'poison': [30, 'enemy', 'infinite', 'full'],
        'cleanse': [20, 'ally', 'infinite', 'full'],
        'purge': [20, 'enemy', 'infinite', 'full'],
        'invigorate': [40, 'ally', 'infinite', 'full'],
        'heal': [40, 'ally', 'infinite', 'full'],
        'mana gift': [30, 'ally', 'infinite', 'full'],
        'morale raise': [30, 'ally', 'infinite', 'full'],
        'regenerate': [40, 'ally', 'infinite', 'full'],
        'novices thunder': [50, 'enemy', 'infinite', 'full'],
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
# shield raise: damage reduction increase
# life bond: taking damage for allies
# magic shield: blocking next status_effect application
# powershot: bow attack + push back
# piercing shot: bow attack + bow attack to target behind
# swirl: axe attack to all targets available
# novices thunder: very weak attack spell with insane gains through level up

# inkscape images of wizards
# wizards with different weapons
# load images based on weapon
# team 1: black drawing on white background
# team 2: white drawing on black background

# a dictionary with the connection between abilities and their respective applied status_effects
status_effect_dict = {'freeze': ['frozen', 'debuff'],
        'burn': ['burning', 'debuff'],
        'manaburn': ['manaburning', 'debuff'],
        'poison': ['poisoned', 'debuff'],
        'regenerate': ['regenerating', 'buff'],
        'invigorate': ['invigorated', 'buff'],
        'stun': ['stunned', 'debuff']}

# a dictionary mapping weapon to its base_damage
weapon_dict = {'longsword': 30,
        'sword and shield': 20,
        'axe': 30,
        'axe and buckler': 20,
        'spear': 20,
        'bow': 20,
        'magic staff': 10,
        'wand and buckler': 5}

# a dictionary with the available upgrades for an Ability
ability_upgrades_dict = {'freeze': ['stunning freeze', 'everlasting freeze', 'freeze blade'],
        'burn': ['stacking burn', 'everlasting burn', 'burn blade'],
        'quick attack': ['remove manacost', 'damage increase'],
        'heal': ['heal all', 'cleanse', 'stronger heal'],
        'cleanse': ['cleanse all', 'cleanse debuffs', 'quicken'],
        'purge': ['purge all', 'purge buffs', 'quicken'],
        'double attack': ['triple attack', 'increase damage', 'reduce manacost'],
        'morale raise': ['cleanse', 'quicken'],
        'novices thunder': ['purge', 'reduce manacost', 'quicken', 'increase damage', 'add strike', 'add random target'],
        'manaburn': ['mana steal', 'strong manaburn', 'manaburn blade']}

class Ability():
    def __init__(self, name):
        self.base = name
        self.upgrades = [name]
        try:
            self.possible_upgrades = ability_upgrades_dict[name]
            self.level_up_experience = 2
        except KeyError:
            self.level_up_experience = np.infty
        self.manacost = ability_dict[name][0]
        self.target_type = ability_dict[name][1]
        self.reach = ability_dict[name][2]
        self.time_usage = ability_dict[name][3]
        self.experience = 0
        self.level = 1
    def level_up(self, upgrade):
        if upgrade == 'remove manacost':
            self.manacost = 0.
        if upgrade == 'reduce manacost':
            self.manacost = 0.5 * self.manacost
        try:
            self.possible_upgrades.pop(self.possible_upgrades.index(upgrade))
            if not self.possible_upgrades:
                self.level_up_experience = np.infty
            self.upgrades.append(upgrade)
        except ValueError:
            pass

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
    damage_reduction_front = 0.
    damage_reduction_side = 0.

    def __init__(self, team, abilities, weapon, **kwargs):
        super().__init__(**kwargs)
        self.health = self.max_health
        self.mana = self.max_mana
        self.t = random.randint(0,99)
        self.team = team
        self.abilities = [Ability('move'), Ability('attack')]
        for abil in abilities:
            self.abilities.append(Ability(abil))
        self.abilities.append(Ability('pass'))
        self.weapon = weapon
        self.base_damage = weapon_dict[weapon]
        if weapon == 'sword and shield':
            self.damage_reduction_front = 0.5
            self.damage_reduction_side = 0.25
        if weapon == 'axe and buckler' or weapon == 'wand and buckler':
            self.damage_reduction_front = 0.2
            self.damage_reduction_side = 0.1

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
                    self.remove_status_effect(child)
            except AttributeError:
                pass
        for child in self.children:
            try:
                if child.mode == 'freeze blade' or child.mode == 'burn blade' or child.mode == 'manaburn blade':
                    target.create_status_effect(child.ability, self)
            except AttributeError:
                pass
        target.change_health(damage, 0)

    def ma_on_release(self):
        self.show_details_popup()

    def show_details_popup(self):
        ''' open an InfoPopup that shows all the details about the character '''
        popup = InfoPopup(self)
        popup.open()

    def create_status_effect(self, ability, source):
        ''' add a new status_effect to the Mate '''
        status_effect_found = False
        for child in self.children:
            if type(child) is StatusEffect:
                if child.mode == status_effect_dict[ability.base][0]:
                    child.apply_status_effect(ability, source, self)
                    status_effect_found = True
        if status_effect_found == False:
            self.add_widget(StatusEffect(ability, source, self))

    def remove_status_effect(self, status_effect):
        ''' remove a StatusEffect by reference '''
        status_effect.remove_status_effect()

    def remove_random_status_effect(self, sign=True):
        ''' remove a single StatusEffect from the Mate, can be discriminated by sign '''
        print('Mate.remove_random_status_effect called')
        status_effects = self.get_status_effects()
        if not sign:
            status_effects = [status_effect for status_effect in status_effects if status_effect.sign == sign]
        if status_effects:
            self.remove_widget(random.choice(status_effects))

    def remove_status_effects(self, sign=True):
        ''' remove all StatusEffects from the Mate, or discriminate by sign '''
        status_effects = self.get_status_effects()
        print(status_effects)
        if not sign:
            status_effects = [status_effect for status_effect in status_effects if status_effect.sign == sign]
        for status_effect in status_effects:
            self.remove_status_effect(status_effect)

    def get_status_effects(self):
        ''' get a list of all StatusEffects applied '''
        return [child for child in self.children if type(child) is StatusEffect]

    def create_select_button(self, source, ability):
        ''' create a SelectButton on this Mate, so that it can be selected as a target by other Mates '''
        self.add_widget(SelectButton(source, ability))

    def push_back(self, target):
        ''' push an enemy Mate back '''
        # bug: pushes over borders
        self_index = self.parent.children[:].index(self)
        target_index = self.parent.children[:].index(target)

        self_row = self_index%cols
        self_col = (self_index-self_row)/cols

        target_row = target_index%cols
        target_col = (target_index-target_row)/cols

        if self_row == target_row:
            if self_col < target_col:
                push = cols
            else:
                push = -cols
        elif self_col == target_col:
            if self_row < target_row:
                push = 1
            else:
                push = -1
        elif self_row < target_row:
            if self_col < target_col:
                push = cols+1
            else:
                push = -cols+1
        elif self_row > target_row:
            if self_col > target_col:
                push = -cols-1
            else:
                push = cols-1
        print('push: {}'.format(push))

        push_index = target_index + push
        print('push_index: {}'.format(push_index))
        print('target_index: {}'.format(target_index))

        if type(self.parent.children[:][push_index]) is EmptyField:
            self.parent.switch_positions(target_index, push_index)

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
            #index_list.remove(index)

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
                if type(child) is Mate:
                    child.create_select_button(self, ability)

    def start_ability(self, ability):
        ''' initiate the target selection '''
        self.create_select_buttons(ability)

    def end_ability(self, ability, target):
        ''' end the ability selection, performing the ability here '''
        self.change_mana(ability.manacost, 0)
        ability.experience += 1
        if ability.experience >= ability.level_up_experience:
            ability.level += 1
            ability.experience = 0
            popup = LevelUpPopup(ability)
            popup.open()
        if ability.target_type == 'move':
            self.parent.switch_positions_by_ref(self, target)
        elif ability.base == 'shield bash':
            self.attack(target, 0.5*self.base_damage)
            self.push_back(target)
        elif ability.base == 'stab back':
            self.attack(target, 0.5*self.base_damage)
            self.push_back(target)
        elif ability.base == 'rookie charge' or ability.base == 'bishop charge':
            self.parent.switch_positions_by_ref(self, target)
        elif ability.base == 'pass':
            self.change_health(0, 10)
            self.change_mana(0, 10)
        elif ability.base == 'heal':
            healing = 30
            if 'stronger heal' in ability.upgrades:
                healing = 50
            if 'heal all' in ability.upgrades:
                for child in self.parent.children[:]:
                    if type(child) is Mate and child.team == self.team:
                        target.change_health(0, healing)
            else:
                target.change_health(0, healing)
        elif ability.base == 'mana gift':
            target.change_mana(0, 30)
        elif ability.base == 'morale raise':
            target.t += 0.5 * (target.max_t - target.t)
            if 'cleanse' in ability.upgrades:
                target.remove_random_status_effect(sign='debuff')
        elif ability.base == 'novices thunder':
            damage = 5
            if 'increase damage' in ability.upgrades:
                damage = 10
            possible_targets = self.parent.children[:]
            possible_targets = [target for target in possible_targets if type(target) == Mate and self.team != target.team]
            targets = [target]
            if 'add random target' in ability.upgrades:
                targets.append(random.choice(possible_targets))
            for target in targets:
                target.change_health(damage, 0)
                if 'purge' in ability.upgrades:
                    target.remove_random_status_effect(sign='buff')
        elif ability.base == 'cleanse':
            sign = True
            if 'cleanse debuffs' in ability.upgrades:
                sign = 'debuff'
            if 'cleanse all' in ability.upgrades:
                target.remove_status_effects(sign=sign)
            else:
                target.remove_random_status_effect(sign=sign)
        elif ability.base == 'purge':
            sign = True
            if 'purge buffs' in ability.upgrades:
                sign = 'buff'
            if 'steal' in ability.upgrades:
                print('not yet implemented')
            if 'purge all' in ability.upgrades:
                target.remove_status_effects(sign=sign)
            else:
                target.remove_random_status_effect(sign=sign)
        elif ability.base == 'summon ghost':
            self.parent.create_ghost(self.team, target)
        elif ability.base == 'attack' or ability == 'knights attack':
            self.attack(target, self.base_damage)
        elif ability.base == 'axe pull':
            self.parent.switch_positions_by_ref(self, target)
            self.attack(target, self.base_damage)
        elif ability.base == 'mana strike':
            damage = (1. + 0.02 * self.mana) * self.base_damage
            self.attack(target, damage)
            self.mana = 0.0
        elif ability.base == 'quick attack':
            modifier = 0.5
            if 'increase damage' in ability.upgrades:
                modifier = 0.75
            self.attack(target, modifier*self.base_damage)
        elif ability.base == 'double attack':
            modifier = 0.6
            if 'increase damage' in ability.upgrades:
                modifier = 0.8
            self.attack(target, modifier * self.base_damage)
            self.attack(target, modifier * self.base_damage)
            if 'triple attack' in ability.upgrades:
                self.attack(target, modifier * self.base_damage)
        elif ability.base == 'electrocute':
            self.attack(target, 2.*self.base_damage)
            target.t += 0.5 * (target.max_t - target.t)
        else:
            target.create_status_effect(ability, self)
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
        if ability.time_usage == 'half' or 'quicken' in ability.upgrades:
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

class LevelUpButton(Button):
    ''' Button in LevelUpPopup '''
    upgrade = StringProperty()
    def __init__(self, upgrade, popup, **kwargs):
        super().__init__(**kwargs)
        self.upgrade = upgrade
        self.popup = popup
    def lub_on_release(self):
        self.popup.ability.level_up(self.upgrade)
        self.popup.dismiss()

class LevelUpLayout(BoxLayout):
    ''' Layout in the LevelUpPopup '''
    def __init__(self, ability, popup, **kwargs):
        super().__init__(**kwargs)
        for upgrade in ability.possible_upgrades:
            self.add_widget(LevelUpButton(upgrade, popup))

class LevelUpPopup(Popup):
    ''' a Popup used to level up an Ability '''
    def __init__(self, ability, **kwargs):
        super().__init__(**kwargs)
        self.ability = ability
        self.add_widget(LevelUpLayout(ability, self))

class InfoPopup(Popup):
    ''' a Popup showing some information about the Mate '''
    team_label = StringProperty()
    health_label = StringProperty()
    mana_label = StringProperty()
    time_label = StringProperty()
    weapon_label = StringProperty()
    status_effect_label = StringProperty()
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
            self.abilities_label += ability.base + ' ( lvl: ' + str(ability.level) + ' / exp: ' + str(ability.experience) + '/' + str(ability.level_up_experience) + ')' + '\n'
        self.status_effect_label = "active status_effects: \n"
        for child in mate.children:
            if type(child) is StatusEffect:
                self.status_effect_label += child.mode + '(' + str(child.stacks) + ') remaining time: ' + str(child.t) + '\n'

class StatusEffect(Widget):
    ''' a widget used to save permanent and temporary changes (status_effects/destatus_effects) on a Mate '''
    t = 0.
    stacks = 0
    def __init__(self, ability, source, target, **kwargs):
        super().__init__(**kwargs)
        self.ability = ability
        self.mode = status_effect_dict[ability.base][0]
        self.sign = status_effect_dict[ability.base][1]
        self.apply_status_effect(ability, source, target)

    def apply_status_effect(self, ability, source, target):
        self.stacks += 1
        self.t += 200.

        if ability.base == 'freeze':
            if 'stunning freeze' in ability.upgrades:
                target.create_status_effect(Ability('stun'), self)
            else:
                target.t = 0.5 * target.t
            if 'everlasting freeze' in ability.upgrades:
                self.t = np.infty
            target.max_t += 10

        if ability.base == 'burn':
            if 'everlasting burn' in ability.upgrades:
                self.t = np.infty

        if ability.base == 'manaburn':
            manacost = 30
            if 'strong manaburn' in ability.upgrades:
                manacost = 60
            if 'mana steal' in ability.upgrades:
                source.change_mana(0, min(manacost, target.mana))
            target.change_mana(manacost, 0)

        if ability.base == 'stun':
            self.t = np.infty

    def remove_status_effect(self):
        print('StatusEffect.remove_status_effect called')
        if self.mode == 'frozen':
            mem_t = self.parent.t / self.parent.max_t
            self.parent.max_t -= self.stacks * 10
            self.parent.t = mem_t * self.parent.max_t
            print(self.parent.t)
            print(self.parent.max_t)
        self.parent.remove_widget(self)

    def update(self, *args):
        game = App.get_running_app().root
        if game.is_running:
            self.t -= 1
            if self.mode == 'poisoned':
                self.parent.change_health(0, -2.*self.parent.health_regen)
            if self.mode == 'regenerating':
                self.parent.change_health(0, self.stacks*self.parent.health_regen)
            if self.mode == 'burning':
                if 'stacking burn' in self.ability.upgrades:
                    self.parent.change_health(self.stacks*0.2, 0)
                else:
                    self.parent.change_health(0.2, 0)
            if self.mode == 'manaburning':
                self.parent.change_health(0, -self.stacks*self.parent.mana_regen)
            if self.mode == 'stunned':
                self.parent.t -= 2.
                if self.parent.t < 0:
                    self.remove_status_effect()
            if self.t < 0.:
                self.remove_status_effect()

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
        self.create_mate(1, ['shield bash', 'burn'], 'axe', 1)
        self.create_mate(2, ['novices thunder', 'burn'], 'axe', 3)

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

