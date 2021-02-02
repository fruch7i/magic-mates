from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty, NumericProperty, BoundedNumericProperty, StringProperty
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.factory import Factory

import random
import numpy as np

# this global parameter is used to switch back and forth between the two possible states of the game, deciding upon a move (False), or running (True)
game_is_running = True

def distance(x, y):
    return np.sqrt( (x[0]-y[0])**2 + (x[1]-y[1])**2)

class Buff(Widget):
    ''' a Widget that stores the behaviour of buffs, can be applied to characters '''
    exists = False
    stacks = 0
    value = 0
    t = 0
    def __init__(self, buff_type, **kwargs):
        super().__init__(**kwargs)
        self.buff_type = buff_type

    def update(self):
        if self.exists:
            self.t -= 1
            if self.t < 0:
                self.remove_buff()
            if self.buff_type == 'burn':
                self.parent.change_health(- self.value * self.stacks)
            if self.buff_type == 'manaburn':
                try:
                    self.parent.change_mana(- self.value * self.stacks)
                except ValueError:
                    self.parent.mana = 0
 
    def add_buff(self):
        self.exists = True
        self.stacks += 1

        if self.buff_type == 'burn':
            self.value = 0.1
            self.t += 300

        elif self.buff_type == 'electrocute':
            self.t += 500
            self.value = 10
            if self.parent.max_t > 30:
                self.parent.max_t -= self.value
            else:
                self.stacks -= 1
            self.parent.t = self.parent.max_t - 1
            self.parent.change_health( -0.75 * random.random() * self.parent.max_t )

        elif self.buff_type == 'poison':
            self.t += 300
            self.stacks = 1

        elif self.buff_type == 'freeze':
            self.t = np.infty
            self.value = 10
            self.parent.t = self.parent.t / 2
            self.parent.max_t += self.value

        elif self.buff_type == 'manaburn':
            self.t += 300
            self.value = 0.1
            try:
                self.parent.change_mana(-50)
            except ValueError:
                self.parent.mana = 0

        else: # this applies to enrage, survivor, freeze, burn and manaburn blade
            self.t = np.infty

    def remove_buff(self):
        if self.buff_type == 'freeze':
            self.parent.max_t -= self.stacks * self.value

        if self.buff_type == 'electrocute':
            self.parent.max_t += self.stacks * self.value

        self.exists = False
        self.stacks = 0
        self.value = 0
        self.t = 0

class PlayingField(FloatLayout):
    ''' the playing field where characters can move along '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_game()

    def update(self, *args):
        for child in self.children:
            try:
                child.update()
            except AttributeError:
                pass

    def create_character(self, pos):
        char = Character()
        char.pos = pos
        self.add_widget(char)

    def create_ghost(self, pos):
        char = Character()
        char.pos = pos
        char.base_dmg = 10
        char.max_health = 80
        char.health = 80
        char.max_mana = 80
        char.mana = 80
        self.add_widget(char)
    
    def start_game(self):
        ''' just a placeholder atm '''
#        self.add_widget(Character(pos=(self.pos[0]+50,self.pos[1]+50))) 
#        self.add_widget(Character(pos=(self.pos[0]+100,self.pos[1]+50)))
#        self.add_widget(Character(pos=(self.pos[0]+100,self.pos[1]+100)))
#        self.add_widget(Character(pos=(self.pos[0]+300,self.pos[1]+100)))

class BasicLayout(BoxLayout):
    ''' this BasicLayout is just a BoxLayout passing the update function from the game to the PlayingField '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update(self):
        for child in self.children:
            try:
                child.update()
            except AttributeError:
                pass

class Menu(BoxLayout):
    ''' the menu where one can choose special abilities and maybe later view detailed info about characters, buffs etc'''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Ability(object):
    def __init__(self, abil_type, **kwargs):
        self.abil_type = abil_type
        self.exists = True
        abil_dict = {'pass': [0, None],
            'freeze': [20, np.infty],
            'electrocute': [30, np.infty],
            'burn': [30, np.infty],
            'manaburn': [10, np.infty],
            'poison': [20, np.infty],
            'debuff': [20, np.infty],
            'teleport': [30, None],
            'quick attack': [20, 80],
            'triple attack': [50, 80],
            'attack all': [40, 80],
            'enrage': [30, np.infty],
            'survivor': [80, np.infty],
            'create ghost': [80, None],
            'freeze blade': [50, 80],
            'burn blade': [50, 80],
            'manaburn blade': [50, 80]}
        self.manacost = abil_dict[abil_type][0]
        self.reach = abil_dict[abil_type][1]

class Character(Button):
    ''' the base class for characters, the mages moving on the PlayingField'''
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

    #team = random.choose([0,1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.health = self.max_health
        self.mana = self.max_mana
        self.t = random.randint(0,99)
        
        self.buff_dict = {
            'burn': Buff('burn'),
            'freeze': Buff('freeze'),
            'electrocute': Buff('electrocute'),
            'manaburn': Buff('manaburn'),
            'poison': Buff('poison'),
            'enrage': Buff('enrage'),
            'survivor': Buff('survivor'),
            'freeze blade': Buff('freeze blade'),
            'burn blade': Buff('burn blade'),
            'manaburn blade': Buff('manaburn blade')}
        for buff_type, buff in self.buff_dict.items():
            self.add_widget(buff)

        self.abil_dict = {
            'pass': Ability('pass'),
            'freeze': Ability('freeze'),
            'electrocute': Ability('electrocute'),
            'burn': Ability('burn'),
            'manaburn': Ability('manaburn'),
            'poison': Ability('poison'),
            'debuff': Ability('debuff'),
            'teleport': Ability('teleport'),
            'quick attack': Ability('quick attack'),
            'triple attack': Ability('triple attack'),
            'attack all': Ability('attack all'),
            'enrage': Ability('enrage'),
            'survivor': Ability('survivor'),
            'create ghost': Ability('create ghost'),
            'freeze blade': Ability('freeze blade'),
            'burn blade': Ability('burn blade'),
            'manaburn blade': Ability('manaburn blade')}

    def update(self, *args):
        '''performing a time step, this includes regenerating health and mana, and updating the time counter'''
        global game_is_running
        if game_is_running:
            # health manipulations, regeneration, burn etc
            if self.buff_dict['poison'].exists:
                self.change_health(-self.health_regen)
            else:
                self.change_health(self.health_regen)
          
            # mana regen
            self.change_mana(self.mana_regen)

            # updating buffs
            for buff_type, buff in self.buff_dict.items():
                buff.update()

            # time counter increase
            self.t += 1
            if self.t > self.max_t:
                game_is_running = False
                self.t = 0
                self.move_prompt()
                self.attack_prompt()
                self.ability_prompt()

    def show_details_popup(self):
        ''' open an InfoPopup that shows all the details about the character '''
        popup = InfoPopup(self)
        popup.open()

    def move(self, direction):
        ''' moving 50 px into the direction given '''
        if direction == 'right':
            self.pos[0] += 50
        elif direction == 'left':
            self.pos[0] -= 50
        elif direction == 'top':
            self.pos[1] += 50
        elif direction == 'bottom':
            self.pos[1] -= 50
        self.end_turn()

    def base_attack(self, target, damage):
        ''' base attack called by attack, attack all, multiattack etc '''
        # add some modifications like freeze and burn on attack
        if self.buff_dict['freeze blade'].exists:
            target.buff_dict['freeze'].add_buff()
        if self.buff_dict['burn blade'].exists:
            target.buff_dict['burn'].add_buff()
        if self.buff_dict['manaburn blade'].exists:
            target.buff_dict['manaburn'].add_buff()
        # deal the damage last, otherwise it may try to change smth on a non-existing character
        if self.buff_dict['enrage'].exists:
            target.change_health( -(self.buff_dict['enrage'].stacks + 1) * damage)
            self.buff_dict['enrage'].stacks -= 1
            if self.buff_dict['enrage'].stacks < 1:
                self.buff_dict['enrage'].remove_buff()
        else:
            target.change_health( - damage )

    def attack(self, target):
        ''' attacking a target '''
        self.base_attack(target, self.base_dmg)
        self.end_turn()

    def change_health(self, change):
        self.health += change
        if self.health > self.max_health:
            self.health = self.max_health
        elif self.health < 0:
            self.die()

    def change_mana(self, change):
        self.mana += change
        if self.mana > self.max_mana:
            self.mana = self.max_mana
        elif self.mana < 0:
            raise ValueError('Mana cannot reach values below 0')

    def die(self):
        for child in self.parent.children:
            if child.buff_dict['survivor']:
                stacks = child.buff_dict['survivor'].stacks
                child.max_health += 2 * stacks
                child.health_regen += 0.002 * stacks
                child.max_mana += 2 * stacks
                child.mana_regen += 0.002 * stacks
                child.base_dmg += 0.5 * stacks
        self.clear_widgets()
        self.parent.remove_widget(self)

    def end_turn(self):
        '''end the turn, remove all MovePrompts, AttackPrompts and AbilityPrompts, restart the clock iteration'''
        # here the [:] copy of the list is important, as otherwise one manipulates the list while iterating over it
        # removing all MovePrompt widgets here
        for child in self.children[:]:
            if type(child) is MovePrompt:
                self.remove_widget(child)

        # removing all AbilityPrompt widgets here
        menu = self.parent.parent.parent.ids['id_menu']
        for child in menu.children[:]:
            if type(child) is AbilityPrompt:
                menu.remove_widget(child)

        # removing all AttackPrompt and ChooseTargetPrompt widgets here
        targets = self.find_neighbours(np.infty)
        for target in targets:
            for child in target.children[:]:
                if type(child) is AttackPrompt:
                    target.remove_widget(child)
                if type(child) is ChooseTargetPrompt:
                    target.remove_widget(child)

        # removing all EmptyFieldPrompt widgets
        for child in self.parent.children[:]:
            if type(child) is EmptyFieldPrompt:
                self.parent.remove_widget(child)

        global game_is_running
        game_is_running = True

    def find_neighbours(self, reach):
        '''find all neighbours of the character within a given reach'''
        siblings = self.parent.children.copy()
        neighbours = []
        for sibling in siblings:
            if distance(self.pos, sibling.pos) < reach:
                neighbours.append(sibling)
        neighbours.remove(self)
        return neighbours

    def move_prompt(self):
        '''creating a MovePrompt button as child of the character for each possible direction'''
        # first check if there are any neighbours blocking the movement
        neighbours = self.find_neighbours(60)
        # these are only direct neighbours, left, right, top and bottom, diagonal neighbours are omitted
        left = True
        right = True
        top = True
        bottom = True
        # check in which directions the neighbour(s) are located
        for neighbour in neighbours:
            if self.pos[0] < neighbour.pos[0]-5:
                right = False
            if self.pos[0] > neighbour.pos[0]+5:
                left = False
            if self.pos[1] < neighbour.pos[1]-5:
                top = False
            if self.pos[1] > neighbour.pos[1]+5:
                bottom = False

        # now add the MovePrompt buttons accordingly, also taking the border of the PlayingField into account
        if (self.pos[1] < 451) & top:
            self.add_widget(MovePrompt(self.pos, 'top'))
        if (self.pos[1] > 1) & bottom:
            self.add_widget(MovePrompt(self.pos, 'bottom'))
        if (self.pos[0] > 1) & left:
            self.add_widget(MovePrompt(self.pos, 'left'))
        if (self.pos[0] < 451) & right:
            self.add_widget(MovePrompt(self.pos, 'right'))

    def attack_prompt(self):
        '''creating an AttackPrompt button as child of the character for each possible target'''
        targets = self.find_neighbours(80)
        for target in targets:
            target.add_widget(AttackPrompt(self, target))

    def ability_prompt(self):
        '''creating an AbilityPrompt button as child of the Menu for each Ability in abil_dict'''
        menu = self.parent.parent.parent.ids['id_menu']
        for abil_type, abil in self.abil_dict.items():
            if abil.exists:
                ability = AbilityPrompt(self, abil_type)
                menu.add_widget(ability)

class InfoPopup(Popup):
    health_label = StringProperty()
    mana_label = StringProperty()
    time_label = StringProperty()
    dmg_label = StringProperty()
    buff_label = StringProperty()
    abil_label = StringProperty()
    def __init__(self, character, **kwargs):
        super().__init__(**kwargs)
        self.health_label = "health: {0:0.1f}/{1:0.1f} regenerating {2:0.2f}".format(character.health, character.max_health, character.health_regen)
        self.mana_label = "mana: {0:0.1f}/{1:0.1f} regenerating {2:0.2f}".format(character.mana, character.max_mana, character.mana_regen)
        self.time_label = "time: {0:0.1f}/{1:0.1f}".format(character.t, character.max_t)
        self.dmg_label = "base damage: {0:0.1f}".format(character.base_dmg)
        self.buff_label = "active Buffs: \n"
        for buff_type, buff in character.buff_dict.items():
            if buff.exists:
                self.buff_label += buff_type + '(' + str(buff.stacks) + ') remaining time: ' + str(buff.t) + '\n'
        self.abil_label = "Abilities: \n"
        for abil_type, abil in character.abil_dict.items():
            if abil.exists:
                self.abil_label += abil_type + "    "

class MovePrompt(Button):
    ''' a button that allows to chose the direction of a movement '''
    def __init__(self, pos, direction, **kwargs):
        '''initializing a properly sized and positioned move prompt button for the requested direction'''
        super().__init__(**kwargs)
        self.direction = direction
        if direction == 'right':
            self.pos = (pos[0] + 50, pos[1])
            self.size = (25, 45)
        elif direction == 'left':
            self.pos = (pos[0] - 30, pos[1])
            self.size = (25, 45)
        elif direction == 'top':
            self.pos = (pos[0], pos[1] + 50)
            self.size = (45, 25)
        elif direction == 'bottom':
            self.pos = (pos[0], pos[1] - 30)
            self.size = (45, 25)

    def move_character(self):
        ''' moving the character in the requested direction when button is pressed '''
        self.parent.move(self.direction)

class AttackPrompt(Button):
    ''' a button that allows to chose the target of an attack, used as child of the target, passing the source '''
    def __init__(self, source, target, **kwargs):
        super().__init__(**kwargs)
        self.pos = ( target.pos[0] + 15, target.pos[1] + 10 )
        self.source = source

    def attack_character(self):
        ''' letting the source attack the parent of the button when pressed '''
        self.source.attack(self.parent)

class AbilityPrompt(Button):
    ''' a button to choose between abilities, located in the Menu '''
    text = StringProperty('')

    def __init__(self, parent_character, abil_type, **kwargs):
        super().__init__(**kwargs)
        self.parent_character = parent_character
        self.abil_type = abil_type
        self.text = str(abil_type) + ' (' + str(self.parent_character.abil_dict[self.abil_type].manacost) + ')'

    def find_empty_positions(self):
        characters = self.parent.parent.parent.ids['id_playing_field'].children[:]
        pos_list = []
        for x in range(0, 501, 50):
            for y in range(0, 501, 50):
                pos_list.append((x,y))
                for char in characters:
                    if distance(char.pos, (x,y)) < 10:
                        pos_list.remove((x,y))
        return pos_list

    def execute_ability(self):
        try:
            self.parent_character.change_mana(- self.parent_character.abil_dict[self.abil_type].manacost )
            if self.abil_type == 'pass':
                self.parent_character.change_mana(10)
                self.parent_character.t = self.parent_character.max_t / 2
                self.parent_character.end_turn()
            elif self.abil_type == 'attack all':
                for target in self.parent_character.find_neighbours(self.parent_character.abil_dict['attack all'].reach):
                    self.parent_character.base_attack(target, self.parent_character.base_dmg)
                self.parent_character.end_turn()
            elif self.abil_type in ['teleport', 'create ghost']:
               self.empty_field_prompt()
            elif self.abil_type in ['survivor', 'freeze blade', 'burn blade', 'manaburn blade', 'debuff']:
                self.choose_target_prompt(True)
            else:
                self.choose_target_prompt(False)
        except ValueError:
            self.parent_character.change_mana( self.parent_character.abil_dict[self.abil_type].manacost )
            popup = Popup(title='Warning!',
                    content=Label(text='not enough mana!'),
                    size_hint = (None, None),
                    size = (400, 300))
            popup.open()

    def empty_field_prompt(self):
        ''' creates an EmptyFieldPrompt at every empty position on the playing field '''
        for child in self.parent_character.children[:]:
            if type(child) is MovePrompt:
                self.parent_character.remove_widget(child)
        pos_list = self.find_empty_positions()
        for pos in pos_list:
            self.parent_character.parent.add_widget(EmptyFieldPrompt(self.parent_character, pos, self.abil_type))

    def choose_target_prompt(self, targeting_self):
        ''' searches for targets in the reach of the ability, checks if there are valid targets and creates apropriate ChooseTargetPrompts '''
        targets = self.parent_character.find_neighbours(self.parent_character.abil_dict[self.abil_type].reach)
        if targeting_self:
            self.parent_character.add_widget(ChooseTargetPrompt(self.parent_character, self.parent_character, self.abil_type))
        else:
            if not targets:
                 # if there are no targets, give back the mana and popup that there are no valid targets
                self.parent_character.change_mana( self.parent_character.abil_dict[self.abil_type].manacost )
                popup = Popup(title='Warning!',
                        content=Label(text='no targets detected!'),
                        size_hint = (None, None),
                        size = (400, 300))
                popup.open()
                
        for target in targets:
            for child in target.children[:]:
                if type(child) is AttackPrompt:
                    target.remove_widget(child)
            target.add_widget(ChooseTargetPrompt(self.parent_character, target, self.abil_type))

class EmptyFieldPrompt(Button):
    ''' a button to chose an empty field as a target, e.g. for teleport '''
    def __init__(self, source, pos, abil_type, **kwargs):
        super().__init__(**kwargs)
        self.source = source
        self.pos_mem = pos
        self.pos = ( pos[0] + 10, pos[1] + 10 )
        self.abil_type = abil_type

    def execute_ability(self):
        if self.abil_type == 'teleport':
            self.source.pos = self.pos_mem
            self.source.end_turn()
        if self.abil_type == 'create ghost':
            self.source.parent.create_ghost(self.pos_mem)
            self.source.end_turn()

class ChooseTargetPrompt(Button):
    ''' a button to chose the target of an ability '''
    def __init__(self, source, target, abil_type, **kwargs):
        super().__init__(**kwargs)
        self.pos = ( target.pos[0] + 15, target.pos[1] + 10 )
        self.source = source
        self.target = target
        self.abil_type = abil_type

    def execute_ability(self):
        if self.abil_type == 'quick attack':
            self.source.base_attack(self.target, 0.25 * self.source.base_dmg)
            self.source.t = self.source.max_t / 2
        if self.abil_type == 'triple attack':
            self.source.base_attack(self.target, 0.5 * self.source.base_dmg)
            self.source.base_attack(self.target, 0.5 * self.source.base_dmg)
            self.source.base_attack(self.target, 0.5 * self.source.base_dmg)
        elif self.abil_type == 'debuff':
            for buff_type, buff in self.parent_character.buff_dict.items():
                buff.remove_buff()
        else:
            self.target.buff_dict[self.abil_type].add_buff()
        self.source.end_turn()

class MaMaGame(BoxLayout):
    t = NumericProperty(0)
    def update(self, *args):
        global game_is_running
        if game_is_running:
            self.t += 1
            for child in self.children:
                try:
                    child.update()
                except AttributeError:
                    pass

class test_mamaApp(App):
    def build(self):
        game = MaMaGame()
        Clock.schedule_interval(game.update, 1/30.)
        return game

if __name__ == "__main__":
    test_mamaApp().run()
