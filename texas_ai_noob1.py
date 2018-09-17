#! /usr/bin/env python
# -*- coding:utf-8 -*-

# 目前算法比较简单，暂时不考虑 allin的决策， 也不考虑其他玩家决策的影响

# import time
import json
import itertools
import random
import hashlib
from websocket import create_connection

# 下面是一些涉及决策和逻辑的常量
# 精度，用于限制模拟测试的次数
PRECISE_VALUE = 500
# 用于模拟发牌前去掉已知牌
INVALID_INDEX = 100
# 扑克字典，用于牌面值转换为16进制整型值
POKER_DIC = {
    'A': 0xC,
    'K': 0xB,
    'Q': 0xA,
    'J': 0x9,
    'T': 0x8,
    '9': 0x7,
    '8': 0x6,
    '7': 0x5,
    '6': 0x4,
    '5': 0x3,
    '4': 0x2,
    '3': 0x1,
    '2': 0x0
}
SUIT_DIC = {'S': 0, 'H': 1, 'C': 2, 'D': 3}
# 花色suit: Spades = 0, Heart = 1, Club = 2, Diamond = 3
# 点数rank: 2~9,TJQK -> 0~12
# card = suit*13 + rank 这个值为 POKER_CARDS 的 index
POKER_CARDS = [
    "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "TS", "JS", "QS", "KS",
    "AS", "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "TH", "JH", "QH",
    "KH", "AH", "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "TC", "JC",
    "QC", "KC", "AC", "2D", "3D", "4D", "5D", "6D", "7D", "8D", "9D", "TD",
    "JD", "QD", "KD", "AD"
]
# 下面是一些关于用户信息的变量
MY_NAME = "FG8Z02NYGQF6KXPX"  # 玩家名
MY_PLAYER_NAME = ""  # 玩家名对应的hashcode
total_bet = 0
my_round_bet = 0
my_chips = 0
player_survived = 0
round_name = "Deal"
my_reload_count = 0

# pip install websocket-client
ws = "ws://serverIP:POR"


# 将手牌升序排列并且转换为 16 进制表示
def poker_sort_encoding(hands):
    global POKER_DIC
    temp = []
    for i in hands:
        temp.append(POKER_DIC[i])
    temp.sort()
    return temp


# 拿到 5 张手牌，计算这手牌的 rank 值
def get_rank(total_cards):
    # print total_cards
    rank = 0x00000000
    my_type = -1
    is_suited = True
    my_suit = total_cards[0][1]

    for i in range(5):
        if total_cards[i][1] != my_suit:
            is_suited = False
            break

    values = []
    for i in total_cards:
        values.append(i[0])
    value_list = poker_sort_encoding(values)  # 存储 手牌牌值 的 16进制形式 并 升序排列好
    # print value_list

    # Sraight 顺子
    if rank == 0:
        if value_list[0] + 1 == value_list[1] and value_list[1] + 1 == value_list[2] and value_list[2] + 1 == value_list[3] and value_list[3] + 1 == value_list[4]:
            # Straight Flush 同花顺
            if is_suited is True:
                # Royal Flush 皇家同花顺
                if value_list[4] == 0xC:
                    my_type = 9
                    rank = (my_type << 4 * 5) + (value_list[4] << 4 * 4)
                    # print "Now my cards are Royal Flush, Rank is " +
                    # hex(rank) + "\n"
                else:
                    my_type = 8
                    rank = (my_type << 4 * 5) + (value_list[4] << 4 * 4)
                    # print "Now my cards are Straight Flush, Rank is " +
                    # hex(rank) + "\n"
            else:
                my_type = 4
                rank = (my_type << 4 * 5) + (value_list[4] << 4 * 4)
                # print "Now my cards are Straight, Rank is " + hex(rank)
    # Four-of-a-kind 四条
    if rank == 0:
        if value_list[0] == value_list[3]:
            my_type = 7
            rank = (my_type << 4 * 5) + \
                (value_list[2] << 4 * 4) + (value_list[4] << 4 * 3)
            # print "Now my cards are Four-of-a-kind, Rank is " + hex(rank)
            # "\n"
        elif value_list[1] == value_list[4]:
            my_type = 7
            rank = (my_type << 4 * 5) + \
                (value_list[2] << 4 * 4) + (value_list[0] << 4 * 3)
            # print "Now my cards are Four-of-a-kind, Rank is " + hex(rank)
    # Full House 葫芦
    if rank == 0:
        if value_list[0] == value_list[2] and value_list[3] == value_list[4]:
            my_type = 6
            rank = (my_type << 4 * 5) + \
                (value_list[1] << 4 * 4) + (value_list[4] << 4 * 3)
            # print "Now my cards are Full House, Rank is " + hex(rank) + "\n"
        elif value_list[0] == value_list[1] and value_list[2] == value_list[4]:
            my_type = 6
            rank = (my_type << 4 * 5) + \
                (value_list[4] << 4 * 4) + (value_list[0] << 4 * 3)
            # print "Now my cards are Full House, Rank is " + hex(rank)
    # Flush 同花
    if rank == 0:
        if is_suited is True:
            my_type = 6
            rank = (my_type << 4 * 5) + (value_list[4] << 4 * 4) + (
                value_list[3] << 4 * 3) + (value_list[2] << 4 * 2) + (
                    value_list[1] << 4 * 1) + value_list[0]
            # print "Now my cards are Flush, Rank is " + hex(rank)
    # Three-of-a-kind 三条
    if rank == 0:
        if value_list[0] == value_list[2]:
            my_type = 3
            rank = (my_type << 4 * 5) + (value_list[0] << 4 * 4) + (
                value_list[4] << 4 * 3) + (value_list[3] << 4 * 2)
            # print "Now my cards are Three-of-a-kind, Rank is " + hex(rank)
        elif value_list[1] == value_list[3]:
            my_type = 3
            rank = (my_type << 4 * 5) + (value_list[1] << 4 * 4) + (
                value_list[4] << 4 * 3) + (value_list[0] << 4 * 2)
            # print "Now my cards are Three-of-a-kind, Rank is " + hex(rank)
        elif value_list[2] == value_list[4]:
            my_type = 3
            rank = (my_type << 4 * 5) + (value_list[2] << 4 * 4) + (
                value_list[1] << 4 * 3) + (value_list[0] << 4 * 2)
            # print "Now my cards are Three-of-a-kind, Rank is " + hex(rank)
    # Two-pair 两对
    if rank == 0:
        if value_list[0] == value_list[1] and value_list[2] == value_list[3]:
            my_type = 2
            rank = (my_type << 4 * 5) + (value_list[0] << 4 * 4) + (
                value_list[2] << 4 * 3) + (value_list[4] << 4 * 2)
            # print "Now my cards are Two-pair, Rank is " + hex(rank)
        if value_list[0] == value_list[1] and value_list[3] == value_list[4]:
            my_type = 2
            rank = (my_type << 4 * 5) + (value_list[0] << 4 * 4) + (
                value_list[3] << 4 * 3) + (value_list[2] << 4 * 2)
            # print "Now my cards are Two-pair, Rank is " + hex(rank)
        if value_list[1] == value_list[2] and value_list[3] == value_list[4]:
            my_type = 2
            rank = (my_type << 4 * 5) + (value_list[1] << 4 * 4) + (
                value_list[3] << 4 * 3) + (value_list[0] << 4 * 2)
            # print "Now my cards are Two-pair, Rank is " + hex(rank)
    # Pair 对子
    if rank == 0:
        if value_list[0] == value_list[1]:
            my_type = 1
            rank = (my_type << 4 * 5) + (value_list[0] << 4 * 4) + (
                value_list[4] << 4 * 3) + (value_list[3] << 4 * 2) + (
                    value_list[2] << 4 * 1)
            # print "Now my cards are Pair, Rank is " + hex(rank)
        elif value_list[1] == value_list[2]:
            my_type = 1
            rank = (my_type << 4 * 5) + (value_list[1] << 4 * 4) + (
                value_list[4] << 4 * 3) + (value_list[3] << 4 * 2) + (
                    value_list[0] << 4 * 1)
            # print "Now my cards are Pair, Rank is " + hex(rank) + "\n"
        elif value_list[2] == value_list[3]:
            my_type = 1
            rank = (my_type << 4 * 5) + (value_list[2] << 4 * 4) + (
                value_list[4] << 4 * 3) + (value_list[1] << 4 * 2) + (
                    value_list[0] << 4 * 1)
            # print "Now my cards are Pair, Rank is " + hex(rank) + "\n"
        elif value_list[3] == value_list[4]:
            my_type = 1
            rank = (my_type << 4 * 5) + (value_list[3] << 4 * 4) + (
                value_list[2] << 4 * 3) + (value_list[1] << 4 * 2) + (
                    value_list[0] << 4 * 1)
            # print "Now my cards are Pair, Rank is " + hex(rank) + "\n"
    # High card
    if rank == 0:
        my_type = 0
        rank = (value_list[4] << 4 * 4) + (value_list[3] << 4 * 3) + \
            (value_list[2] << 4 * 2) + (value_list[1] << 4 * 1) + value_list[0]
        # print "Now my cards are Pair, Rank is " + hex(rank) + "\n"

    return rank


# 计算牌值, 两张 private, 五张 public。 2+3->5张最后rank最大的手牌
def get_hand_value(private, public):
    # print "now calculate hand value"
    my_ranks = []  # 公共牌 5选3， 10种情况下 最终手牌的牌值
    my_cards = []
    pub_index = []
    for i in private:
        my_cards.append(i)
    # print "These cards are in my hand:" + my_cards[0] + ' ' + my_cards[1] +
    # "\n"

    # 组合处理，将5张公共牌取出3张组成最后的说牌，计算所有情况下的rank，得到最优结果
    pub_index = list(itertools.combinations(range(5), 3))

    for i in range(10):
        total = []
        for j in my_cards:
            total.append(j)
        total.append(public[pub_index[i][0]])
        total.append(public[pub_index[i][1]])
        total.append(public[pub_index[i][2]])
        my_ranks.append(get_rank(total))

    my_ranks.sort()  # 排序后返回最后一位，即最大值
    return my_ranks[-1]


# 计算手牌的力量，即反复调用 get_hand_value() 从而得到胜过别人的概率
# 返回值 为 浮点型
def get_hand_strenth(data):
    print "now calculate hand strenth"
    global PRECISE_VALUE, INVALID_INDEX, POKER_DIC, SUIT_DIC, POKER_CARDS
    global player_survived
    my_score = 0
    # ramain_cards 里储存的是对应 POKER_CARDS 里的索引
    remain_cards = range(52)
    my_cards = []
    public_cards = []
    public_cards_number = 0
    displayed_cards = []
    # 取出玩家手牌和公共牌，并且放在一起组织为已知牌
    for i in data["self"]["cards"]:
        my_cards.append(i)
        displayed_cards.append(i)
    if data["game"]["board"]:
        for i in data["game"]["board"]:
            public_cards.append(i)
            public_cards_number += 1
            displayed_cards.append(i)
    # 将已知牌从牌组中抽出，得到剩余牌，这里是剩余牌的索引
    for i in displayed_cards:
        rank = 0
        rank += SUIT_DIC[i[1]] * 13
        rank += POKER_DIC[i[0]]
        remain_cards[rank] = INVALID_INDEX
    remain_cards.sort()
    while remain_cards[-1] > 52:
        remain_cards.pop(-1)

    del displayed_cards

    for times in range(PRECISE_VALUE):
        # 将剩余牌的index进行排序，这里用了 random库里集成的 knuth shuffle
        random.shuffle(remain_cards)
        pseudo_public = []
        for c in public_cards:
            pseudo_public.append(c)
        count = 0
        hand_value_list = []
        # 将 公共牌补满 5张
        while count < 5 - public_cards_number:
            pseudo_public.append(POKER_CARDS[remain_cards[count]])
            count += 1
        my_hand_value = get_hand_value(my_cards, pseudo_public)
        hand_value_list.append(my_hand_value)
        # 分别给剩下的人分配手牌，并把他们的牌值放入 hand_value_list中
        for i in range(player_survived - 1):
            other_cards = []
            for j in range(2):
                other_cards.append(POKER_CARDS[remain_cards[count]])
                count += 1
            hand_value_list.append(get_hand_value(other_cards, pseudo_public))
        hand_value_list.sort()
        # print hex(hand_value_list[-1])
        # 如果自己手牌的模拟值取得最大，则给我的分数上加上 1/有同等手牌的人数
        if my_hand_value == hand_value_list[-1]:
            win_player_num = 1
            # print "player survived: " + str(player_survived)
            while win_player_num <= player_survived and my_hand_value == hand_value_list[0 - win_player_num]:
                win_player_num += 1
            # print "win_player_num: " + str(win_player_num)
            my_score += (1 / (win_player_num - 1))
        # print times
    hand_strenth = float(my_score) / float(PRECISE_VALUE)
    print "hand_strenth:" + str(hand_strenth)
    return hand_strenth


# 计算回报率，手牌强度和赔率的比，并以此决定是否采取何种 action, 返回值为一个包含 [回报率，手牌力量] 的 list
def get_return_rate(data):
    print "now calculate return rate"
    global total_bet, my_round_bet
    pot_oods = 0
    return_rate = 0
    bet = data["self"]["bet"]
    hs = get_hand_strenth(data)
    print "my round bet: " + str(my_round_bet)
    print "current bet: " + str(bet)
    print "my chips: " + str(my_chips)
    if total_bet != 0 and my_round_bet + bet != 0:
        pot_oods = float(my_round_bet + bet) / \
            float(total_bet)  # 赔率，即下注和总奖池金额的比
    else:
        pot_oods = 1.00  # 如果我当前还没有下注，也不需要下注，那么暂且认为赔率为 1， 即后面得到的回报率 = 手牌强度
    return_rate = hs / pot_oods  # 回报率
    rr = [return_rate, hs]
    print "pot oods:" + str(pot_oods)
    print "return_rate: " + str(return_rate)
    return rr


# 选择行动，根据回报率按照一定概率采取行动, 需要考虑筹码保护的问题， 主要为 fold, call, raise,check
def choose_action_FCR(data):
    print "now choose action_FCR"
    global MY_PLAYER_NAME, round_name
    return_rate_list = get_return_rate(data)
    return_rate = return_rate_list[0]
    hand_strenth = return_rate_list[1]
    if round_name == "Deal":  # 第一轮发牌，未知公共牌，，以手牌强度作为主要判断依据
        if hand_strenth < 0.15:
            if random.random() < 0.40:
                ws.send(
                    json.dumps({
                        "eventName": "__action",
                        "data": {
                            "action": "fold"
                        }
                    }))
                print "Action: Fold"
            else:
                ws.send(
                    json.dumps({
                        "eventName": "__action",
                        "data": {
                            "action": "call"
                        }
                    }))
                print "Action: Call"
        else:
            if random.random() < 0.05:
                ws.send(
                    json.dumps({
                        "eventName": "__action",
                        "data": {
                            "action": "fold"
                        }
                    }))
                print "Action: Fold"
            else:
                ws.send(
                    json.dumps({
                        "eventName": "__action",
                        "data": {
                            "action": "call"
                        }
                    }))
                print "Action: Call"
    else:  # 其他轮，以 return_rate 作为决策标准
        if need_stack_protection(data, hand_strenth):
            ws.send(
                json.dumps({
                    "eventName": "__action",
                    "data": {
                        "action": "fold"
                    }
                }))
            print "Action: Fold"
        else:
            if return_rate < 0.8:
                if random.random() < 0.95:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "fold"
                            }
                        }))
                    print "Action: Fold"
                else:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "raise"
                            }
                        }))
                    print "Action: Raise"
            elif return_rate < 1.0:
                if random.random() < 0.80:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "fold"
                            }
                        }))
                    print "Action: Fold"
                elif random.random() < 0.85:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "call"
                            }
                        }))
                    print "Action: Call"
                else:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "raise"
                            }
                        }))
                    print "Action: Raise"
            elif return_rate < 1.3:
                if random.random() < 0.60:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "call"
                            }
                        }))
                    print "Action: Call"
                else:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "raise"
                            }
                        }))
                    print "Action: Raise"
            else:
                if random.random() < 0.30:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "call"
                            }
                        }))
                    print "Action: Call"
                else:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "raise"
                            }
                        }))
                    print "Action: Raise"


# 这部分重写　！！！
# 选择行动，根据回报率按照一定概率采取行动, 需要考虑筹码保护的问题， 主要为 bet, check
def choose_action_BC(data):
    print "now choose action_BC"
    global MY_PLAYER_NAME
    return_rate_list = get_return_rate(data)
    return_rate = return_rate_list[0]
    hand_strenth = return_rate_list[1]
    min_bet = data["self"]["minBet"]
    if need_stack_protection(data, hand_strenth):
        ws.send(
            json.dumps({
                "eventName": "__action",
                "data": {
                    "action": "fold"
                }
            }))
        print "Action: Fold"
    else:
        if hand_strenth > 0.7:
            if return_rate > 1.0:
                if random.random() < 0.6:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "bet",
                                "amount": min_bet * 4
                            }
                        }))
                    print "Action: Bet"
                else:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "check"
                            }
                        }))
                    print "Action: Check"
            else:
                if random.random() > 0.6:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "bet",
                                "amount": min_bet * 4
                            }
                        }))
                    print "Action: Bet"
                else:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "check"
                            }
                        }))
                    print "Action: Check"
        elif hand_strenth > 0.3:
            if return_rate > 1.0:
                if random.random() < 0.6:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "bet",
                                "amount": min_bet * 2
                            }
                        }))
                    print "Action: Bet"
                else:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "check"
                            }
                        }))
                    print "Action: Check"
            else:
                if random.random() > 0.6:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "bet",
                                "amount": min_bet * 2
                            }
                        }))
                    print "Action: Bet"
                else:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "check"
                            }
                        }))
                    print "Action: Check"
        else:
            if return_rate > 1.3:
                if random.random() < 0.2:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "bet",
                                "amount": min_bet
                            }
                        }))
                    print "Action: Bet"
                else:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "check"
                            }
                        }))
                    print "Action: Check"
            else:
                if random.random() > 0.6:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "bet",
                                "amount": min_bet
                            }
                        }))
                    print "Action: Bet"
                else:
                    ws.send(
                        json.dumps({
                            "eventName": "__action",
                            "data": {
                                "action": "fold"
                            }
                        }))
                    print "Action: Fold"


# 是否需要索取筹码, 暂时不用这个函数， 目前看来还是默认没有筹码再自动索取比较好，\
# 人工智障Dummy是一开始就全拿下来了，这样的情况是赚的多赔的快，风险较大，在有更好的处理办法前，不管它
# 这里存在一些问题，我写的很简单就是，当钱最少的时候索取筹码，但是当 当前筹码不足以继续跟注等复杂情况没有考虑
def need_reload(data):
    print "now determin whether to reload"
    global MY_PLAYER_NAME, my_chips
    # chip_list = []
    # reload_count = 0
    # for i in data["players"]:
    #     chip_list.append(i["chips"])
    #     if i["playerName"] == MY_PLAYER_NAME:
    #         reload_count = i["reloadCount"]
    # chip_list.sort()
    # my_chips = data["players"][MY_PLAYER_NAME]["chips"]
    # if my_chips < 100 and my_chips == chip_list[0] and reload_count < 2:
    #     ws.send(json.dumps({
    #         "eventName": "__reload"
    #     }))
    if my_chips == 0:
        print "Action: Reload"


# 筹码保护的决策
def need_stack_protection(data, hand_strenth):
    global my_reload_count
    # print my_reload_count
    if my_reload_count == 0:
        bet = data["self"]["minBet"]
        small_blind = data["game"]["smallBlind"]["amount"]
        if my_chips - bet < small_blind * 4 and hand_strenth < 0.5:
            return True
        else:
            return False
    elif my_reload_count == 1:
        if random.random() < 0.5:
            bet = data["self"]["minBet"]
            small_blind = data["game"]["smallBlind"]["amount"]
            if my_chips - bet < small_blind * 4 and hand_strenth < 0.5:
                return True
            else:
                return False
    else:
        return False


# 每次系统广播消息(不用回复)时 更新 本地信息 !
def update_local_data(action, data):
    # print "now update local data"
    global MY_PLAYER_NAME, total_bet, my_round_bet, my_chips, round_name
    global player_survived, my_reload_count
    # 每次有人行动的时候， 更新记录奖池总金额， 统计场上还活着的人的数量
    if action == "__show_action":
        if data["table"]["totalBet"]:
            total_bet = data["table"]["totalBet"]
        player_survived = 0
        for i in data["players"]:
            if i["isSurvive"] is True:
                player_survived = player_survived + 1
        # print "player_survived: " + str(player_survived)
    # 新一轮开始的时候， 将本地总奖池金额归零， 然后记录我的本轮投注和持有的筹码数， 以及场上活着的人数
    elif action == "__new_round":
        total_bet = 0
        player_survived = 0
        for i in data["players"]:
            if i["isSurvive"] is True:
                player_survived += 1
            if i["playerName"] == MY_PLAYER_NAME:
                my_chips = i["chips"]
                my_round_bet = i["roundBet"]
                my_reload_count = i["reloadCount"]
            # print "player_survived: " + str(player_survived)
        round_name = data["table"]["roundName"]
    elif action == "__deal":
        round_name = data["table"]["roundName"]
        print round_name
        # print my_chips
        for i in data["players"]:
            if i["playerName"] == MY_PLAYER_NAME:
                my_chips = i["chips"]
                my_round_bet = i["roundBet"]
                break


# 根据 event_name 将 data 传入不同的响应函数
def takeAction(action, data):
    if action == "__start_reload":
        # need_reload(data)
        pass
    elif action == "__bet":
        choose_action_BC(data)
    elif action == "__action":
        choose_action_FCR(data)
    else:
        update_local_data(action, data)


def doListen():
    try:
        # 建立与服务器连接，join加入游戏
        global ws, MY_PLAYER_NAME, MY_NAME
        global MY_NAME, MY_PLAYER_NAME
        MY_PLAYER_NAME = hashlib.md5()
        MY_PLAYER_NAME.update(MY_NAME.encode('utf-8'))
        ws = create_connection("ws://10.64.8.41/")
        ws.send(
            json.dumps({
                "eventName": "__join",
                "data": {
                    "playerName": MY_NAME
                }
            }))

        # 死循环 监听服务器信息
        while 1:
            result = ws.recv()
            msg = json.loads(result)
            event_name = msg["eventName"]
            data = msg["data"]
            print event_name
            # print data
            takeAction(event_name, data)
    except Exception, e:
        print e.message
        doListen()


if __name__ == '__main__':
    doListen()
