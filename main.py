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
from kivy.uix.screenmanager import ScreenManager, Screen

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
        'shield raise': [30, 'ally', 'self', 'full'],
        'shield bash': [30, 'enemy', 'sword and shield', 'full'],
        'stab back': [30, 'enemy', 'spear', 'full'],
        'powershot': [30, 'enemy', 'bow', 'full'],
        'multishot': [30, 'all enemies', 'bow', 'full'],
        'knights move': [20, 'move', 'knight', 'half'],
        'teleport': [50, 'move', 'infinite', 'full'],
        'summon zombie': [50, 'summon', 'axe', 'full'],
        'summon golem': [50, 'summon', 'axe', 'full'],
        'summon ghost': [50, 'summon', 'axe', 'full'],
        'summon vampire': [50, 'summon', 'axe', 'full'],
        'summon shadow': [100, 'summon', 'axe', 'full'],
        'pass': [0, 'self', 'self', 'half'],
        'attack': [0, 'enemy', 'weapon', 'full'],
        'pierce attack': [40, 'enemy', 'weapon', 'full'],
        'axe pull': [30, 'enemy', 'weapon', 'full'],
        'shield breaker': [40, 'enemy', 'weapon', 'full'],
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
        'health gift': [25, 'ally', 'infinite', 'full'],
        'mana gift': [30, 'ally', 'infinite', 'full'],
        'morale raise': [30, 'ally', 'infinite', 'full'],
        'regenerate': [40, 'ally', 'infinite', 'full'],
        'novices thunder': [50, 'enemy', 'infinite', 'full'],
        'vampiric bite': [30, 'enemy', 'weapon', 'full'],
        'sacrificial attack': [30, 'enemy', 'weapon', 'full'],
        'stun': [40, 'enemy', 'infinite', 'full']}

# ToDo, add:
# improve target handling of allies, enemies, self, all mates etc

# flanking bonus damage:
# bonus damage if allies are on opposing sides

# new abilities:
# life bond: taking damage for allies
# magic shield: blocking next status_effect application
# multishot: bow attack to all available targets
# swirl: axe attack to all targets available
# novices thunder: very weak attack spell with insane gains through level up

# inkscape images of wizards
# wizards with different weapons
# load images based on weapon
# team 1: black drawing on white background
# team 2: white drawing on black background

# a dictionary with the connection between abilities and their respective applied status_effects and their sign
status_effect_dict = {'freeze': ['frozen', 'debuff'],
        'burn': ['burning', 'debuff'],
        'manaburn': ['manaburning', 'debuff'],
        'poison': ['poisoned', 'debuff'],
        'shield raise': ['shield raised', 'buff'],
        'shield breaker': ['shield broken', 'debuff'],
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
        'shield raise': ['raise all', 'counter attack', 'cleanse'],
        'double attack': ['triple attack', 'increase damage', 'reduce manacost'],
        'morale raise': ['cleanse', 'quicken'],
        'novices thunder': ['purge', 'reduce manacost', 'quicken', 'increase damage', 'add strike', 'add random target'],
        'manaburn': ['mana steal', 'strong manaburn', 'manaburn blade']}

def get_direction(mate1, mate2):
    ''' get the direction between two mates, used for shields damage reduction '''
    mate1_index = mate1.parent.children[:].index(mate1)
    mate2_index = mate2.parent.children[:].index(mate2)

    mate1_col = mate1_index%cols
    mate1_row = (mate1_index-mate1_col)/cols

    mate2_col = mate2_index%cols
    mate2_row = (mate2_index-mate2_col)/cols

    if mate1_row == mate2_row:
        return 'side'
    if mate1_row > mate2_row:
        if mate1.team > mate2.team:
            return 'front'
        else: return 'back'
    if mate1_row < mate2_row:
        if mate1.team > mate2.team:
            return 'back'
        else: return 'front'

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
    health_regen = 0.02

    max_armor = 100.0
    armor = NumericProperty(1.0)

    max_mana = 100.0
    mana = NumericProperty(1.0)
    mana_regen = 0.1

    team = NumericProperty(0)
    weapon = StringProperty('')
    base_damage = 0
    damage_reduction_front = 0.
    damage_reduction_side = 0.

    armor_block_front = 0.66
    armor_block_side = 0.33

    button_normal_path = StringProperty('')

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
            self.armor = self.max_armor
        elif 'buckler' in weapon:
            self.damage_reduction_front = 0.2
            self.damage_reduction_side = 0.1
            self.armor = 0.66 * self.max_armor
        else:
            self.armor = 0.33 * self.max_armor
        self.button_normal_path = 'gfx/' + str(self.team) + '_' + self.weapon.replace(' ', '_') + '.png'
        
    def change_health(self, damage, heal, source = None, pierce = False):
        if pierce:
            armor_block_front = 0.
            armor_block_side = 0.
        else:
            armor_block_front = self.armor_block_front
            armor_block_side = self.armor_block_side

        if source:
            if get_direction(self, source) == 'front':
                damage = (1-self.damage_reduction_front) * damage
                armor_damage = armor_block_front * damage
                damage = (1-armor_block_front) * damage
            elif get_direction(self, source) == 'side':
                damage = (1-self.damage_reduction_side) * damage
                armor_damage = armor_block_side * damage
                damage = (1-armor_block_side) * damage
            else:
                armor_damage = 0
        else:
            armor_damage = 0
        if armor_damage > self.armor:
            damage += armor_damage - self.armor
            self.armor = 0
        else:
            self.armor -= armor_damage
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

    def attack(self, target, damage, pierce = False):
        ''' attacking a target Mate '''
        self_status_effects = [child for child in self.children if type(child) == StatusEffect]
        target_status_effects = [child for child in target.children if type(child) == StatusEffect]
        for status_effect in self_status_effects:
            mode = status_effect.mode
            if mode == 'invigorated':
                damage = status_effect.stacks * damage
                self.remove_status_effect(status_effect)
            if mode == 'freeze blade' or mode == 'burn blade' or mode == 'manaburn blade':
                target.create_status_effect(status_effect.ability, self)
        for status_effect in target_status_effects:
            mode = status_effect.mode
            if mode == 'shield raise':
                if 'counter attack' in status_effect.ability.upgrades:
                    self.change_health(target.base_damage, 0, source = target)
                    # bug: counter attack has infinite reach, does not apply ability blades and also triggers from backside
        target.change_health(damage, 0, source = self, pierce = pierce)

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
        status_effects = self.get_status_effects()
        if not sign:
            status_effects = [status_effect for status_effect in status_effects if status_effect.sign == sign]
        if status_effects:
            self.remove_widget(random.choice(status_effects))

    def remove_status_effects(self, sign=True):
        ''' remove all StatusEffects from the Mate, or discriminate by sign '''
        status_effects = self.get_status_effects()
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

        push_index = target_index + push

        if type(self.parent.children[:][push_index]) is EmptyField:
            self.parent.switch_positions(target_index, push_index)

    def create_select_buttons(self, ability):
        ''' create select buttons based on the ability used '''
        index = self.parent.children[:].index(self)
        if ability.reach == 'weapon':
            reach = self.weapon
        else:
            reach = ability.reach

        if 'sword' in reach:
            index_list = self.parent.get_sword_index(self, ability.target_type)
        elif 'axe' in reach:
            index_list = self.parent.get_axe_index(self, ability.target_type)
        elif 'spear' in reach:
            index_list = self.parent.get_spear_index(self, ability.target_type)
        elif 'bow' in reach:
            index_list = self.parent.get_queen_index(self, ability.target_type)
        elif 'knight' in reach:
            index_list = self.parent.get_knight_index(self, ability.target_type)
        elif reach == 'rook':
            index_list = self.parent.get_rook_index(self, ability.target_type)
        elif reach == 'bishop':
            index_list = self.parent.get_bishop_index(self, ability.target_type)
        elif reach == 'infinite' or reach == 'magic staff' or reach == 'wand and buckler':
            index_list = list(range(0, cols**2))
        elif reach == 'self':
            self.end_ability(ability, self)
            index_list = []

        # create SelectButtons based on weather the abilities targeting type is move, enemy, ally or all mates
        for i in index_list:
            child = self.parent.children[i]
            if ability.target_type == 'move' or 'summon' in ability.target_type:
                if type(child) is EmptyField:
                    child.create_select_button(self, ability)
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
        if ability.target_type == 'self' or ability.target_type == 'all enemies' or ability.target_type == 'all allies':
            self.end_ability(ability, None)
        else:
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
        elif ability.base == 'powershot':
            self.attack(target, 0.5*self.base_damage)
            self.push_back(target)
        elif ability.base == 'multishot':
            target_indices = self.parent.get_queen_index(self, ability.target_type)
            targets = [self.parent.children[i] for i in target_indices]
            for target in targets:
                self.attack(target, self.base_damage)
        elif ability.base == 'swirl':
            targets = self.parent.get_axe_index(self, ability.target_type)
            for target in targets:
                self.attack(target, self.base_damage)
        elif ability.base == 'rookie charge' or ability.base == 'bishop charge':
            self.parent.switch_positions_by_ref(self, target)
        elif ability.base == 'pass':
            self.change_health(0, 5)
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
        elif ability.base == 'health gift':
            target.change_health(0, 30)
            self.change_health(30, 0)
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
                target.change_health(damage, 0, source = self)
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
        elif 'summon' in ability.base:
            self.parent.create_summon(self.team, target, ability)
        elif ability.base == 'attack' or ability == 'knights attack':
            self.attack(target, self.base_damage)
        elif ability.base == 'vampiric bite':
            self.attack(target, self.base_damage)
            self.change_health(0, self.base_damage)
        elif ability.base == 'sacrificial attack':
            self.attack(target, 2*self.base_damage)
            self.change_health(self.base_damage, 0, pierce = True)
        elif ability.base == 'pierce attack':
            self.attack(target, self.base_damage, pierce = True)
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
        game = App.get_running_app().root.board.ids['game']
        menu = game.ids['ability_menu']
        for ability in self.abilities:
            menu.create_ability_prompt(self, ability)

    def end_turn(self, ability):
        ''' end the turn by resetting t and game.is_running, and removing all AbilityPrompts '''
        if ability.time_usage == 'full':
            self.t = 0.
        elif ability.time_usage == 'half' or 'quicken' in ability.upgrades:
            self.t = 0.5 * self.max_t
        else:
            print('Error, ability.time_usage not valid')
        game = App.get_running_app().root.board.ids['game']
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
        game = App.get_running_app().root.board.ids['game']
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

        if ability.base == 'shield breaker':
            target.damage_reduction_front = 0.
            target.damage_reduction_side = 0.

        if ability.base == 'shield raise':
            target.damage_reduction_front *= 1.5
            target.damage_reduction_side *= 1.5

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
        if self.mode == 'frozen':
            mem_t = self.parent.t / self.parent.max_t
            self.parent.max_t -= self.stacks * 10
            self.parent.t = mem_t * self.parent.max_t

        if self.mode == 'shield broken' or self.mode == 'shield raised':
            weapon = self.target.weapon
            if weapon == 'sword and shield':
                target.damage_reduction_front = 0.5
                target.damage_reduction_side = 0.25
            if weapon == 'axe and buckler' or weapon == 'wand and buckler':
                target.damage_reduction_front = 0.2
                target.damage_reduction_side = 0.1

        self.parent.remove_widget(self)

    def update(self, *args):
        game = App.get_running_app().root.board.ids['game']
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
        self.start_new_game()
        
    def start_new_game(self):
        self.create_mate(1, ['rookie charge', 'axe pull', 'invigorate'], 'axe', 1)
        self.create_mate(1, ['shield raise', 'heal', 'cleanse'], 'sword and shield', 2)
        self.create_mate(1, ['summon zombie', 'summon ghost', 'freeze'], 'magic staff', 4)
        self.create_mate(1, ['multishot', 'pierce attack', 'knights move'], 'bow', 5)

        self.create_mate(2, ['pierce attack', 'sacrificial attack', 'bishop charge'], 'longsword', 47)
        self.create_mate(2, ['stab back', 'quick attack', 'double attack'], 'spear', 46)
        self.create_mate(2, ['pierce attack', 'sacrificial attack', 'purge'], 'axe and buckler', 44)
        self.create_mate(2, ['manaburn', 'burn', 'summon golem'], 'wand and buckler', 43)

    def adjust_target_type(self, mate, index_list, target_type):
        if target_type == 'move' or target_type == 'summon':
            return [index for index in index_list if type(self.children[index]) == EmptyField]
        else:
            index_list = [index for index in index_list if type(self.children[index]) == Mate]
            if 'enemy' in target_type:
                index_list = [index for index in index_list if mate.team != self.children[index].team]
            if 'ally' in target_type:
                index_list = [index for index in index_list if mate.team == self.children[index].team]
            if 'self' in target_type:
                index_list.append(self.children[:].index(mate))
            return index_list

    def get_sword_index(self, mate, target_type):
        index = self.children[:].index(mate)
        index_list = [index+1, index-1, index+cols, index-cols]
        index_list = [i for i in index_list if i >= 0 and i < cols**2] # remove upper and lower borders
        if index%cols == 0:
            index_list = [i for i in index_list if i%cols <= 2] # remove right border
        if index%cols == cols-1:
            index_list = [i for i in index_list if i%cols >= cols-3] # remove left border
        return self.adjust_target_type(mate, index_list, target_type)

    def get_axe_index(self, mate, target_type):
        index = self.children[:].index(mate)
        index_list = [index+1, index-1, index+cols, index-cols, index+1+cols, index-1+cols, index+1-cols, index-1-cols]
        index_list = [i for i in index_list if i >= 0 and i < cols**2] # remove upper and lower borders
        if index%cols == 0:
            index_list = [i for i in index_list if i%cols <= 2] # remove right border
        if index%cols == cols-1:
            index_list = [i for i in index_list if i%cols >= cols-3] # remove left border
        return self.adjust_target_type(mate, index_list, target_type)

    def get_spear_index(self, mate, target_type):
        index = self.children[:].index(mate)
        index_list = [index+1, index-1, index+2, index-2, index+cols, index-cols, index+2*cols, index-2*cols, index+1+cols, index-1+cols, index+1-cols, index-1-cols]
        index_list = [i for i in index_list if i >= 0 and i < cols**2] # remove upper and lower borders
        if index%cols == 0 or index%cols == 1:
            index_list = [i for i in index_list if i%cols <= 3] # remove right border
        if index%cols == cols-1 or index%cols == cols-2:
            index_list = [i for i in index_list if i%cols >= cols-4] # remove left border
        return self.adjust_target_type(mate, index_list, target_type)

    def get_knight_index(self, mate, target_type):
        index = self.children[:].index(mate)
        index_list = [index+cols+2, index+cols-2, index+2*cols+1, index+2*cols-1, index-cols+2, index-cols-2, index-2*cols+1, index-2*cols-1]
        index_list = [i for i in index_list if i >= 0 and i < cols**2] # remove upper and lower borders
        if index%cols == 0 or index%cols == 1:
            index_list = [i for i in index_list if i%cols <= 3] # remove right border
        if index%cols == cols-1 or index%cols == cols-2:
            index_list = [i for i in index_list if i%cols >= cols-4] # remove left border
        return self.adjust_target_type(mate, index_list, target_type)

    def get_bishop_index(self, mate, target_type):
        index = self.children[:].index(mate)
        col = index%cols
        row = (index-col)/cols
        index_list = []
        top_left = True
        top_right = True
        bot_left = True
        bot_right = True
        if index%cols == cols-1:
            top_left = False
            bot_left = False
        if index%cols == 0:
            top_right = False
            bot_right = False
        if index < cols:
            bot_left = False
            bot_right = False
        if index > cols**2-cols:
            top_left = False
            top_right = False
        for i in range(1, cols+2):
            if top_left:
                new_index = index+i+i*cols
                index_list.append(new_index)
                if new_index%cols == cols-1 or new_index >= cols**2-cols or type(self.children[new_index]) == Mate:
                    top_left = False
            if top_right:
                new_index = index-i+i*cols
                index_list.append(new_index)
                if new_index%cols == 0 or new_index >= cols**2-cols or type(self.children[new_index]) == Mate:
                    top_right = False
            if bot_left:
                new_index = index+i-i*cols
                index_list.append(new_index)
                if new_index%cols == cols-1 or new_index <= cols or type(self.children[new_index]) == Mate:
                    bot_left = False
            if bot_right:
                new_index = index-i-i*cols
                index_list.append(new_index)
                if new_index%cols == 0 or new_index <= cols or type(self.children[new_index]) == Mate:
                    bot_right = False
        return self.adjust_target_type(mate, index_list, target_type)

    def get_rook_index(self, mate, target_type):
        index = self.children[:].index(mate)
        col = index%cols
        row = (index-col)/cols
        index_list = []
        top = True
        right = True
        bot = True
        left = True
        if index%cols == cols-1:
            left = False
        if index%cols == 0:
            right = False
        if index < cols:
            bot = False
        if index > cols**2-cols:
            top = False
        for i in range(1, cols+2):
            if top:
                new_index = index+i*cols
                index_list.append(new_index)
                if new_index >= cols**2-cols or type(self.children[new_index]) == Mate:
                    top = False
            if bot:
                new_index = index-i*cols
                index_list.append(new_index)
                if new_index < cols-1 or type(self.children[new_index]) == Mate:
                    bot = False
            if left:
                new_index = index+i
                index_list.append(new_index)
                if new_index%cols == cols-1 or type(self.children[new_index]) == Mate:
                    left = False
            if right:
                new_index = index-i
                index_list.append(new_index)
                if new_index%cols == 0 or type(self.children[new_index]) == Mate:
                    right = False
        index_list = [index for index in index_list if index >= 0 and index < cols**2]
        return self.adjust_target_type(mate, index_list, target_type)

    def get_queen_index(self, mate, target_type):
        bishop_index = self.get_bishop_index(mate, target_type)
        rook_index = self.get_rook_index(mate, target_type)
        return list(set(rook_index + bishop_index))

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

    def create_summon(self, team, target, ability):
        ''' create a new Mate with lower stats '''
        if ability.base == 'summon zombie':
            summon = Mate(team, ['poison'], 'axe')
            summon.max_health = 50
            summon.health = 50
            summon.max_armor = 25
            summon.armor = 0
            summon.max_mana = 50
            summon.mana = 0
            summon.weapon = 'axe'
            summon.base_damage = 25
        elif ability.base == 'summon vampire':
            summon = Mate(team, ['vampiric bite', 'sacrificial attack'], 'axe')
            summon.max_health = 100
            summon.health = 50
            summon.max_armor = 50
            summon.armor = 0
            summon.max_mana = 100
            summon.mana = 0
            summon.weapon = 'axe'
            summon.base_damage = 15
        elif ability.base == 'summon ghost':
            summon = Mate(team, ['health gift', 'mana gift'], 'magic staff')
            summon.max_health = 20
            summon.health = 20
            summon.max_armor = 10
            summon.armor = 0
            summon.max_mana = 50
            summon.mana = 50
            summon.weapon = 'magic staff'
            summon.base_damage = 5
        elif ability.base == 'summon golem':
            summon = Mate(team, ['shield raise'], 'sword and shield')
            summon.max_health = 100
            summon.health = 100
            summon.max_armor = 100
            summon.armor = 100
            summon.max_mana = 100
            summon.mana = 0
            summon.max_t = 150
            summon.weapon = 'magic staff'
            summon.base_damage = 15

        summon.health_regen = 0
        summon.t = 1.

        self.add_widget(summon)
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
        game = App.get_running_app().root.board.ids['game']
        if game.is_running:
            self.t += 1
        for child in self.children:
            try:
                child.update(*args)
            except AttributeError:
                pass

class MagicMatesGame(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_running = True
    def update(self, *args):
        for child in self.children:
            try:
                child.update(*args)
            except AttributeError:
                pass

class MenuScreen(Screen):
    pass

class BoardScreen(Screen):
    def update(self, *args):
        for child in self.children:
            try:
                child.update(*args)
            except AttributeError:
                pass

class UpdatingScreenManager(ScreenManager):
    menu = None
    board = None
    def quit_game(self):
        App.get_running_app().stop()
    def update(self, *args):
        for child in self.children:
            try:
                child.update(*args)
            except AttributeError:
                pass

class magicmatesApp(App):
    def build(self):
        sm = UpdatingScreenManager()
        Clock.schedule_interval(sm.update, 1/60.)
        sm.menu = MenuScreen(name='menu')
        sm.board = BoardScreen(name='board')
        sm.add_widget(sm.menu)
        sm.add_widget(sm.board)
        return sm

if __name__ == "__main__":
    magicmatesApp().run()

