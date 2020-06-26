import sys
import time
# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.
TURN = 1
USE_ITEMS = True
VALUES = {
    'B': 0,
    'C': 0.5,
    'D': 0.5,
    'G': 2,
    'L': 3,
    'W': 1,
    '-': 0
}
my_hand = list()
my_board = list()
opponent_board = list()


class Player:
    def __init__(self, player_health, player_mana, player_deck, player_rune, player_draw):
        self.hp = player_health
        self.mana = player_mana
        self.deck = player_deck
        self.rune = player_rune
        self.draw = player_draw


class Card:
    def __init__(self, card_number, inst_id, location, type, cost, attack, defense, abilities, mhc, ohc, carddraw,
                 can_play, can_summon):
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
        self.can_summon = can_summon

    def value(self):
        return 0


class Creature(Card):
    def __init__(self, card_number, inst_id, location, type, cost, attack, defense, abilities, mhc, ohc, carddraw,
                 can_play, can_summon):
        super().__init__(card_number, inst_id, location, type, cost, attack, defense, abilities, mhc, ohc, carddraw,
                         can_play, can_summon)

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
                 can_play, can_summon):
        super().__init__(card_number, inst_id, location, type, cost, attack, defense, abilities, mhc, ohc, carddraw,
                      can_play, can_summon)

    def draft_value(self):
        x = 0
        if self.card_type == 1:
            for a in self.abilities:
                x += VALUES[a]
            x += 1.5 * self.attack + 2 * self.defense
            if self.cost != 0:
                x /= self.cost
        elif self.card_type == 2:
            for a in self.abilities:
                x += VALUES[a]
            x += abs(self.attack) + 1.5 * abs(self.defense)
            if self.cost != 0:
                x /= self.cost
        return x

    def value(self):
        x = 0
        if self.card_type == 1:
            for a in self.abilities:
                x += VALUES[a]
            x += 2 * self.attack + 3 * self.defense
        elif self.card_type == 2:
            for a in self.abilities:
                x += VALUES[a]
            x += 1.25 * abs(self.attack) + 1.75 * abs(self.defense)
        return x


def dynamic_knapsack_algorithm(elements, weight):
    weight += 1
    used_cards = list()

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

    tmp = weight - 1
    for e in range(len(elements)-1, -1, -1):
        if b[e][tmp][0] == 1:                             # this item is in the knapsack
            used_cards.append(elements[e])
            tmp -= elements[e].cost
    return used_cards


def card_pick(cards):
    max_value = 0
    nb = -1
    is_item = False
    if USE_ITEMS:
        for i in range(3):
            if cards[i].draft_value() > max_value:
                max_value = cards[i].draft_value()
                nb = i
    else:
        for i in range(3):
            if isinstance(cards[i], Creature):
                if cards[i].draft_value() > max_value:              # picking the most valuable Creature
                    max_value = cards[i].draft_value()
                    nb = i
    if nb == -1:
        return "PASS"
    return "PICK " + str(nb)


def summon_card(player):
    global my_hand, my_board, opponent_board
    guard_on_board = False
    guard_in_hand = False
    cards_possible_to_summon = list()
    commands = list()
    for card in my_hand:                                       # checking Guard on board and in hand
        if isinstance(card, Creature) and card.abilities.find("G") != -1:
            guard_in_hand = True
    for card in my_board:
        if isinstance(card, Creature) and card.abilities.find("G") != -1:
            guard_on_board = True
    if (not guard_on_board) and guard_in_hand:                  # summon Guards first
        my_hand.sort(key=lambda v: v.value(), reverse=True)
        for card in my_hand:
            if isinstance(card, Creature) and card.abilities.find("G") != -1 and card.cost <= player.mana:
                commands.append("SUMMON " + str(card.instance_id))
                player.mana -= card.cost
                card.can_summon = False
                my_board.append(card)
    for card in my_hand:
        if card.can_summon:
            cards_possible_to_summon.append(card)

    summoned_cards = dynamic_knapsack_algorithm(cards_possible_to_summon, player.mana)      # summon cards
    summoned_cards.sort(key=lambda t: t.card_type)
    for card in summoned_cards:
        if isinstance(card, Creature):
            if card.abilities.find("C") != -1:                     # if summoned card is Charge, it can attack this turn
                card.can_play = True
            my_board.append(card)
            commands.append("SUMMON " + str(card.instance_id))
        elif isinstance(card, Item):                                # use item
            if (card.card_type == 1 and len(my_board) > 0) or (card.card_type == 2 and len(opponent_board) > 0):
                commands.append(use_item(card))
    if len(summoned_cards) and len(commands) == 0:
        return "PASS"
    return ";".join(commands)


def use_item(item):
    global my_hand, my_board, opponent_board
    my_guards = list()
    target_id = 0
    for card in my_board:
        if card.abilities.find("G") != -1:
            my_guards.append(card)
    my_board.sort(key=lambda v: v.value(), reverse=True)
    my_guards.sort(key=lambda v: v.value(), reverse=True)
    if item.card_type == 1:                                         # green item
        if item.attack == 0:                                        # Guard priority
            if len(my_guards) > 0:
                target_id = my_guards[0].instance_id
        elif item.defense >= item.attack and len(my_guards) > 0:
            for card in my_board:
                if card.instance_id == my_guards[0].instance_id:
                    card.attack += item.attack
                    card.defense += item.defense
                    target_id = card.instance_id
        else:
            target_id = my_board[0].instance_id
        return "USE " + str(item.instance_id) + " " + str(target_id)
    if item.card_type == 2:                                         # red item
        opponent_guards = list()
        for card in opponent_board:
            if card.abilities.find("G") != -1:
                opponent_guards.append(card)
        opponent_board.sort(key=lambda v: v.attack, reverse=True)
        opponent_guards.sort(key=lambda v: v.defense, reverse=True)
        if len(opponent_guards) > 0:
            for guard in opponent_guards:
                if guard.defense <= abs(item.defense):                    # if can kill any guard, do it
                    opponent_board.remove(guard)
                    return "USE " + str(item.instance_id) + " " + str(guard.instance_id)
                elif item.abilities.find("G") != -1:                    # if can remove Guard, do it
                    for card in opponent_board:
                        if card.instance_id == guard.instance_id:
                            opponent_board[0].attack += item.attack
                            opponent_board[0].defense += item.defense
                            return "USE " + str(item.instance_id) + " " + str(guard.instance_id)
        for card in opponent_board:                            # if can't kill guard, but can kill any other card, do it
            if card.defense <= abs(item.defense):
                opponent_board.remove(card)
                return "USE " + str(item.instance_id) + " " + str(card.instance_id)

        opponent_board[0].attack += item.attack                           # if can't kill any
        opponent_board[0].defense += item.defense
        return "USE " + str(item.instance_id) + " " + str(opponent_board[0].instance_id)
    return "USE -1"


def subsets(s, elements):
    subset = list()
    mask = 1
    for i in range(len(elements)):
        if mask & s > 0:
            subset.append(elements[i])
        mask = mask << 1
    return subset


def attacking(player, opponent):
    global my_board, opponent_board
    opponent_guards = list()
    commands = list()
    guards_killed = 0
    is_ward = False
    lethals_on_board = 0

    for card in opponent_board:                                         # checking if opponent has a guard
        if card.abilities.find("G") != -1:
            opponent_guards.append(card)

    for card in my_board:
        if card.abilities.find("L") != -1:
            lethals_on_board += 1

    my_board.sort(key=lambda v: v.value(), reverse=True)
    opponent_board.sort(key=lambda v: v.value(), reverse=True)
    opponent_guards.sort(key=lambda v: v.value(), reverse=True)

    if len(opponent_board) == 0:                                    # if opponent has no cards on board, attack directly
        for card in my_board:
            if card.can_play:
                c = "ATTACK " + str(card.instance_id) + " -1"
                commands.append(c)
        return ";".join(commands)

    i = 0
    if len(opponent_guards) > 0:                                     # attacking guards first
        for card in opponent_guards:
            j = -1
            if card.abilities.find("W") != -1:
                is_ward = True
            if is_ward:                                   # if Guard is also a Ward, attack with the least valuable card
                commands.append("ATTACK " + str(my_board[-1].instance_id) + " " + str(card.instance_id))
                my_board[-1].can_play = False

            all_subsets_of_cards = list()  # generating all subsets of player's cards on board
            m = 2 ** len(my_board)
            for s in range(m):
                all_subsets_of_cards.append(subsets(s, my_board))

            best_attack = [[0 for i in range(6)], 10, False]                 # [cards to attack, ... ,is Guard dead]
            is_dead = False
            for c in all_subsets_of_cards:
                sum = 0
                for s in range(len(c)):
                    if c[s].can_play:
                        sum += c[s].attack
                difference = sum - card.defense
                if difference >= 0:
                    if best_attack[2]:
                        if len(c) < len(best_attack[0]) and difference < best_attack[1]:
                            best_attack = [c, difference, True]
                    else:
                        best_attack = [c, difference, True]
                else:
                    if not best_attack[2]:
                        if len(c) < len(best_attack[0]) and difference < best_attack[1]:
                            best_attack = [c, difference, False]

            while (not is_dead) and i < len(my_board):
                if lethals_on_board > 0:                            # killing Guard with Lethal
                    if my_board[i].abilities.find("L") != -1:
                        c = "ATTACK " + str(my_board[i].instance_id) + " " + str(card.instance_id)
                        commands.append(c)
                        card.defense -= my_board[i].attack
                        my_board[i].can_play = False
                        lethals_on_board -= 1
                        is_dead = True

                elif my_board[i].can_play:                          # attacking Guard
                    if my_board[i].abilities.find("G") != -1:
                                                # if player's card is Guard, attack only if can kill opponent's Guard
                        if my_board[i].attack >= card.defense and card.attack < my_board[i].defense:
                            c = "ATTACK " + str(my_board[i].instance_id) + " " + str(card.instance_id)
                            commands.append(c)
                            card.defense -= my_board[i].attack
                    else:
                        c = "ATTACK " + str(my_board[i].instance_id) + " " + str(card.instance_id)
                        commands.append(c)
                        card.defense -= my_board[i].attack
                        my_board[i].can_play = False
                    if card.defense <= 0:
                        is_dead = True
                        guards_killed += 1
                i += 1

    if len(opponent_guards) == guards_killed:
        attack_sum = 0
        opponent_attack_sum = 0
        for card in my_board:
            if card.can_play:
                attack_sum += card.attack
        for card in opponent_board:
            opponent_attack_sum += card.attack
        if attack_sum >= opponent.hp:                       # if opponent is killable this turn, just do it
            for card in my_board:
                if card.can_play:
                    c = "ATTACK " + str(card.instance_id) + " -1"
                    commands.append(c)
            return ";".join(commands)

        if len(my_board) > 2:  # attack opponent's most valuable card (but not with Guard)
            if opponent_board[0].value() > my_board[0].value():
                nb = -1
                for card in my_board:
                    if card.abilities.find("G") == -1:
                        if (card.attack > opponent_board[0].defense and card.defense > opponent_board[0].attack) \
                                and card.can_play:
                            nb = card.instance_id
                            card.can_play = False
                            break
                if nb != -1:
                    c = "ATTACK " + str(nb) + " " + str(opponent_board[0].instance_id)
                    commands.append(c)

        for card in my_board:                                       # attacking opponent
            if card.can_play:
                c = "ATTACK " + str(card.instance_id) + " -1"
                commands.append(c)
                card.can_play = False
        return ";".join(commands)
    else:
        # if opponent still has a guard, can't do anything else this turn
        return ";".join(commands)


def action(cards, player, opponent):
    global my_hand, my_board, opponent_board
    my_hand.clear()
    my_board.clear()
    opponent_board.clear()

    if TURN <= 30:                                                  # draft
        return card_pick(cards)
    commands = list()
    for card in cards:
        if card.location == 0:
            my_hand.append(card)
        elif card.location == 1:
            my_board.append(card)
            card.can_play = True
        elif card.location == -1:
            opponent_board.append(card)
            card.can_play = True

    summon_action = summon_card(player)
    if len(summon_action) == "PASS" and len(my_board) == 0:         # empty board and no summon
        return "PASS"
    if summon_action != "PASS":
        commands.append(summon_action)                              # summoning if possible
    commands.append(attacking(player, opponent))                            # attacking
    return ";".join(commands)


def main():
    # game loop
    global TURN
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
                                 my_health_change, opponent_health_change, card_draw, False, True)
            else:
                karta = Item(card_number, instance_id, location, card_type, cost, attack, defense, abilities,
                             my_health_change, opponent_health_change, card_draw, True, True)
            cards.append(karta)

        command = action(cards, player, opponent)
        TURN += 1
        end = time.clock()
        total = end - start
        print("{0:02f}s".format(total), file=sys.stderr)
        print(command)
    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)


start = time.clock()
main()
