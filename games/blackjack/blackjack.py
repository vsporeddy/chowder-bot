"""
    Let's play black jack with Chowder
"""
import random

class Card:
    def __init__(self, suit, val):
        self.suit = suit
        self.value = val

    def show(self):
        suit_string = self.value
        if(suit_string == 1):
            suit_string = "Ace"
        elif(suit_string == 11):
            suit_string = "Jack"
        elif(suit_string == 12):
            suit_string = "Queen"
        elif(suit_string == 13):
            suit_string = "King"
        return f"{suit_string} of {self.suit}"

class Deck:
    def __init__(self):
        self.cards = []
        self.build()

    def build(self):
        for suit in ["Spades", "Clubs", "Diamonds", "Hearts"]:
            for value in range(1, 14):
                self.cards.append(Card(suit, value))

    def shuffle(self):
        random.shuffle(self.cards)

    def show(self):
        for card in self.cards:
            card.show()

    def draw_card(self):
        return self.cards.pop()

class Player:
    def __init__(self, player):
        self.player = player
        self.hand = []
        self.can_draw = True

    def draw(self, deck):
        if self.can_draw:
            the_card = deck.draw_card()
            self.hand.append(the_card)
            return the_card
        else:
            return None

    def show_hand(self):
        for card in self.hand:
            card.show()

    def set_cant_draw(self):
        self.can_draw = False

async def start(bot, ctx, players):
    await ctx.send(f"Starting a game of **blackjack** with {', '.join([p.mention for p in players])}")
    cgr = bot.get_cog("Cgr")
    winners = await play(bot, ctx, players)
    await cgr.update_ratings_blackjack(ctx, players, winners)
    return winners

async def play(bot, ctx, players):
    dealer = Player(bot.user)
    gamers = []
    deck = Deck()
    deck.shuffle()

    players_cant_draw = 0

    def check(m):
        return m.author in players and \
               (m.content.upper() == "HIT" or \
               m.content.upper() == "STAY")

    for p in players:
        gamers.append(Player(p))

    dealer_card = dealer.draw(deck)
    await ctx.send(f"ChowderTron drew {dealer_card.show()}")

    for g in gamers:
        the_card = g.draw(deck)
        await ctx.send(f"{g.player.display_name} drew {the_card.show()}")
 
    while players_cant_draw < len(gamers):
        deal_message = (await bot.wait_for("message", check=check))
        if (deal_message.content.upper() == "HIT"):
            player_getting_card = get_player(deal_message.author, gamers)
            the_card = player_getting_card.draw(deck)
            
            if the_card is not None:
                await ctx.send(f"{player_getting_card.player.display_name} drew {the_card.show()}")
                bust = get_total_point(player_getting_card)
                await ctx.send(f"{player_getting_card.player.display_name} has {bust}")

                if bust > 21:
                    await ctx.send(f"{player_getting_card.player.display_name} is busted")
                    player_getting_card.set_cant_draw()
                    players_cant_draw += 1
                elif (bust == 21):
                    await ctx.send(f"Nice! {player_getting_card.player.display_name} hit Black Jack")
                    player_getting_card.set_cant_draw()
                    players_cant_draw += 1

        elif(deal_message.content.upper() == "STAY"):
            player_stop = get_player(deal_message.author, gamers)

            if (player_stop.can_draw == True):
                player_stop.set_cant_draw()
                players_cant_draw += 1

    while get_total_point(dealer) < 17:
        dealer_card = dealer.draw(deck)
        await ctx.send(f"ChowderTron drew {dealer_card.show()}")
    
    dealer_point = get_total_point(dealer)
    await ctx.send(f"ChowderTron has {dealer_point}")

    winner = []
    dealer_point = get_total_point(dealer)
    for g in gamers:
        gamer_point = get_total_point(g)
        if ((gamer_point < 22 and dealer_point < gamer_point) or (dealer_point > 21 and gamer_point <= 21)):
            await ctx.send(f"DANG {g.player.display_name}, you beat Chowder")
            winner.append(g.player)

    return winner


def get_total_point(gamer):
    total_point = 0
    count_ace = 0
    for card in gamer.hand:
        if(card.value > 10):
            total_point += 10
        elif(card.value == 1):
            count_ace += 1
            total_point += 1
        else:
            total_point += card.value
    
    while count_ace > 0:
        if(total_point <= 11):
            total_point += 10
        count_ace -= 1

    return total_point



def get_player(author, gamers):
    for g in gamers:
        if (g.player == author):
            return g