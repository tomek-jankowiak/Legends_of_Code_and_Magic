import sys
import math

# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.
TURN = 1
USE_ITEMS = False
VALUES = {
    'B': 0,
    'C': 0,
    'D': 0.5,
    'G': 2,
    'L': 3,
    'W': 1,
    '-': 0
}


class Player:
    def __init__(self, player_health, player_mana, player_deck, player_rune, player_draw):
        self.hp = player_health
        self.mana = player_mana
        self.deck = player_deck
        self.rune = player_rune
        self.draw = player_draw


class Card:
    def __init__(self, card_number, inst_id, location, type, cost, attack, defense, abilities, mhc, ohc, carddraw,
                 can_play):
        self.card_number = card_number
        self.instance_id = inst_id
        self.location = location
        self.card_type = type
        self.cost = cost
        self.attack = attack
        self.defense = defense
        self.abilities = abilities
        self.my_health_change = mhc
        self.opponent_health_change = ohc
        self.card_draw = carddraw
        self.can_play = can_play

    def value(self):
        return 0


class Creature(Card):
    def __init__(self, card_number, inst_id, location, type, cost, attack, defense, abilities, mhc, ohc, carddraw,
                 can_play):
        super().__init__(card_number, inst_id, location, type, cost, attack, defense, abilities, mhc, ohc, carddraw,
                         can_play)

    def draft_value(self):
        x = 0
        for a in self.abilities:
            x += VALUES[a]
        x += 3 * self.attack + self.defense
        if self.cost != 0:
            x /= self.cost
        return x

    def value(self):
        x = 0
        for a in self.abilities:
            x += VALUES[a]
        x += 3 * self.attack + self.defense
        return x


class Item(Card):
    def __init__(self, card_number, inst_id, location, type, cost, attack, defense, abilities, mhc, ohc, carddraw,
                 can_play):
        Card.__init__(self, card_number, inst_id, location, type, cost, attack, defense, abilities, mhc, ohc, carddraw,
                      can_play)


def dynamic_knapsack_algorithm(elements, weight, type_of_action):
    weight += 1
    commands = list()
    summoned_cards = list()
    result = list()

    b = [[[0 for i in range(2)] for j in range(weight)] for k in range(len(elements))]
    # [number of elements][weight][2], last list stores: [0]-is current item put(T/F), [1]-current value of knapsack
    for e in range(len(elements)):
        for w in range(weight):
            if e == 0:                                          # first item
                if elements[e].cost <= w:                       # can put into knapsack
                    b[e][w][0] = 1
                    b[e][w][1] = elements[e].value()
            else:
                if w < elements[e].cost:                        # can't put current item
                    b[e][w][0] = 0
                    b[e][w][1] = b[e-1][w][1]
                else:                                           # put more valuable item
                    if b[e-1][w-elements[e].cost][1] + elements[e].value() >= b[e-1][w][1]:
                        b[e][w][0] = 1
                        b[e][w][1] = b[e-1][w-elements[e].cost][1] + elements[e].value()
                    else:
                        b[e][w][0] = 0
                        b[e][w][1] = b[e-1][w][1]
    # knapsack packed
    if type_of_action == "summon":
        tmp = weight - 1
        for e in range(len(elements)-1, -1, -1):
            w = tmp
            while w >= 0:
                if b[e][w][0] == 1:                             # this item is in the knapsack
                    c = "SUMMON " + str(elements[e].instance_id)
                    commands.append(c)
                    summoned_cards.append(elements[e])
                    tmp -= elements[e].cost
                    w = -1
                w -= 1
    result.append(";".join(commands))
    if type_of_action == "summon":
        result.append(summoned_cards)
    return result


def card_pick(cards):
    max_value = 0
    nb = -1
    if not USE_ITEMS:
        for i in range(3):
            if isinstance(cards[i], Creature):
                if cards[i].draft_value() > max_value:  # picking the most valuable Creature
                    max_value = cards[i].draft_value()
                    nb = i
        if nb == -1:
            return "PASS"
        return "PICK " + str(nb)


def summon_card(my_cards, my_board, player):
    result = list()
    indexes = list()
    c = ""
    guard_on_board = False
    guard_in_hand = False
    for card in my_cards:
        if card.abilities.find("G") != -1:
            guard_in_hand = True
    for card in my_board:
        if card.abilities.find("G") != -1:
            guard_on_board = True
    if (not guard_on_board) and guard_in_hand:
        my_cards.sort(key=lambda v: v.value(), reverse=True)
        for i in range(len(my_cards)):
            if my_cards[i].abilities.find("G") != -1 and my_cards[i].cost <= player.mana:
                c += "SUMMON " + str(my_cards[i].instance_id) + ";"
                player.mana -= my_cards[i].cost
                indexes.append(i)

    if len(indexes) != 0:
        for i in range(len(indexes)):
            my_cards.pop(indexes[i])

    knapsack_result = dynamic_knapsack_algorithm(my_cards, player.mana, "summon")
    for card in knapsack_result[1]:
        player.mana -= card.cost
    summoned_commands = c + knapsack_result[0]
    summoned_cards = knapsack_result[1]
    for card in summoned_cards:
        if card.abilities.find("C") != -1:  # if summoned card is Charge, it can attack this turn
            card.can_play = True
    if len(summoned_commands) == 0:
        result.append("PASS")
    else:
        result.append(summoned_commands)
    result.append(summoned_cards)
    return result


def attacking(my_cards, opponent_cards, opponent):
    opponent_guards = list()
    commands = list()
    guards_killed = 0
    is_ward = False
    lethals_on_board = 0

    for card in opponent_cards:  # checking if opponent has a guard
        if card.abilities.find("G") != -1:
            opponent_guards.append(card)

    for card in my_cards:
        if card.abilities.find("L") != -1:
            lethals_on_board += 1

    my_cards.sort(key=lambda v: v.value(), reverse=True)
    opponent_cards.sort(key=lambda v: v.value(), reverse=True)
    opponent_guards.sort(key=lambda v: v.value(), reverse=True)

    if len(opponent_cards) == 0:  # if opponent has no cards on board, attack directly
        for card in my_cards:
            if card.can_play:
                c = "ATTACK " + str(card.instance_id) + " -1"
                commands.append(c)
        return ";".join(commands)

    i = 0
    if len(opponent_guards) > 0:  # attacking guards first
        for card in opponent_guards:
            j = -1
            if card.abilities.find("W") != -1:
                is_ward = True
            while (is_ward and abs(j) <= len(my_cards)) and my_cards[j].can_play:
                # if Guard is also a Ward, attack with the least valuable card
                if isinstance(my_cards[j], Creature):
                    c = "ATTACK " + str(my_cards[j].instance_id) + " " + str(card.instance_id)
                    commands.append(c)
                    my_cards[j].can_play = False
                    is_ward = False
                j -= 1

            is_dead = False
            while (not is_dead) and i < len(my_cards):
                if lethals_on_board > 0:  # killing Guard with Lethal
                    if my_cards[i].abilities.find("L") != -1:
                        c = "ATTACK " + str(my_cards[i].instance_id) + " " + str(card.instance_id)
                        commands.append(c)
                        card.defense -= my_cards[i].attack
                        my_cards[i].can_play = False
                        lethals_on_board -= 1
                        is_dead = True

                elif my_cards[i].can_play:  # attacking Guard
                    if my_cards[i].abilities.find("G") != -1:
                        # if player's card is Guard, attack only if can kill opponent's Guard
                        if my_cards[i].attack >= card.defense and card.attack < my_cards[i].defense:
                            c = "ATTACK " + str(my_cards[i].instance_id) + " " + str(card.instance_id)
                            commands.append(c)
                            card.defense -= my_cards[i].attack
                    else:
                        c = "ATTACK " + str(my_cards[i].instance_id) + " " + str(card.instance_id)
                        commands.append(c)
                        card.defense -= my_cards[i].attack
                        my_cards[i].can_play = False
                    if card.defense <= 0:
                        is_dead = True
                        guards_killed += 1
                i += 1

    if len(opponent_guards) == guards_killed:
        attack_sum = 0
        for card in my_cards:
            if card.can_play:
                attack_sum += card.attack
        if attack_sum >= opponent.hp:
            for card in my_cards:
                if card.can_play:
                    c = "ATTACK " + str(card.instance_id) + " -1"
                    commands.append(c)
            return ";".join(commands)

        if len(my_cards) > 2:  # attack opponent's most valuable card (but not with Guard)
            if opponent_cards[0].value() > my_cards[0].value():
                nb = -1
                for card in my_cards:
                    if card.abilities.find("G") == -1:
                        if (card.attack > opponent_cards[0].defense and card.defense > opponent_cards[
                            0].attack) and card.can_play:
                            nb = card.instance_id
                            card.can_play = False
                            break
                if nb != -1:
                    c = "ATTACK " + str(nb) + " " + str(opponent_cards[0].instance_id)
                    commands.append(c)

        for card in my_cards:  # attacking opponent
            if card.can_play:
                c = "ATTACK " + str(card.instance_id) + " -1"
                commands.append(c)
                card.can_play = False
        return ";".join(commands)
    else:
        return ";".join(commands)  # if opponent still has a guard, can't do anything else this turn


def action(cards, player, opponent):
    if TURN <= 30:  # draft
        return card_pick(cards)
    my_hand = []
    my_board = []
    opponent_board = []
    for card in cards:
        if card.location == 0:
            my_hand.append(card)
        elif card.location == 1:
            my_board.append(card)
            card.can_play = True
        elif card.location == -1:
            opponent_board.append(card)
            card.can_play = True
    commands = list()
    summon_action = summon_card(my_hand, my_board, player)
    if summon_action[0] != "PASS":
        commands.append(summon_action[0])  # summoning if possible
    for card in summon_action[1]:
        my_board.append(card)
    commands.append(attacking(my_board, opponent_board, opponent))  # attacking
    return ";".join(commands)


# game loop
while True:
    for i in range(2):
        player_health, player_mana, player_deck, player_rune, player_draw = [int(j) for j in input().split()]
        if i == 0:
            player = Player(player_health, player_mana, player_deck, player_rune, player_draw)
        else:
            opponent = Player(player_health, player_mana, player_deck, player_rune, player_draw)

    opponent_hand, opponent_actions = [int(i) for i in input().split()]
    for i in range(opponent_actions):
        card_number_and_action = input()
    card_count = int(input())

    cards = []

    for i in range(card_count):
        card_number, instance_id, location, card_type, cost, attack, defense, abilities, my_health_change, opponent_health_change, card_draw = input().split()
        card_number = int(card_number)
        instance_id = int(instance_id)
        location = int(location)
        card_type = int(card_type)
        cost = int(cost)
        attack = int(attack)
        defense = int(defense)
        abilities = str(abilities)
        my_health_change = int(my_health_change)
        opponent_health_change = int(opponent_health_change)
        card_draw = int(card_draw)
        if card_type == 0:
            karta = Creature(card_number, instance_id, location, card_type, cost, attack, defense, abilities,
                             my_health_change, opponent_health_change, card_draw, False)
        else:
            karta = Item(card_number, instance_id, location, card_type, cost, attack, defense, abilities,
                         my_health_change, opponent_health_change, card_draw, True)
        cards.append(karta)

    command = action(cards, player, opponent)
    TURN += 1
    print(command)
    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)
