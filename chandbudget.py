#!/usr/bin/env python

import sys

from gsp import GSP
from util import argmax_index

class Chandbudget:
    """Balanced bidding agent"""
    def __init__(self, id, value, budget):
        self.id = id
        self.value = value
        self.budget = budget
        self.remaining_budget = budget
        self.TOTAL_NUM_ROUNDS = 48
        self.high_alpha = 1.75

    def initial_bid(self, reserve):
        return self.value / 2


    def slot_info(self, t, history, reserve):
        """Compute the following for each slot, assuming that everyone else
        keeps their bids constant from the previous rounds.

        Returns list of tuples [(slot_id, min_bid, max_bid)], where
        min_bid is the bid needed to tie the other-agent bid for that slot
        in the last round.  If slot_id = 0, max_bid is 2* min_bid.
        Otherwise, it's the next highest min_bid (so bidding between min_bid
        and max_bid would result in ending up in that slot)
        """
        prev_round = history.round(t-1)
        other_bids = filter(lambda (a_id, b): a_id != self.id, prev_round.bids)

        clicks = prev_round.clicks
        def compute(s):
            (min, max) = GSP.bid_range_for_slot(s, clicks, reserve, other_bids)
            if max == None:
                max = 2 * min
            return (s, min, max)
            
        info = map(compute, range(len(clicks)))
#        sys.stdout.write("slot info: %s\n" % info)
        return info


    def expected_utils(self, t, history, reserve):
        """
        Figure out the expected utility of bidding such that we win each
        slot, assuming that everyone else keeps their bids constant from
        the previous round.

        returns a list of utilities per slot.
        """
        # Balanced Budget computation
        info = self.slot_info(t, history, reserve)
        prev_round = history.round(t - 1)

        clicks = prev_round.clicks
        norm = max(clicks)
        pos = map(lambda c: float(c) / norm, clicks)

        utilities = []

        for i in range(len(info)):
            (s, mn, mx) = info[i]
            exp_util = pos[i] * (self.value - mn)
            utilities.append(exp_util)

        return utilities

    def target_slot(self, t, history, reserve):
        """Figure out the best slot to target, assuming that everyone else
        keeps their bids constant from the previous rounds.

        Returns (slot_id, min_bid, max_bid), where min_bid is the bid needed to tie
        the other-agent bid for that slot in the last round.  If slot_id = 0,
        max_bid is min_bid * 2
        """
        i =  argmax_index(self.expected_utils(t, history, reserve))
        info = self.slot_info(t, history, reserve)
        return info[i]

    def bid(self, t, history, reserve):
        # The Balanced bidding strategy (BB) is the strategy for a player j that, given
        # bids b_{-j},
        # - targets the slot s*_j which maximizes his utility, that is,
        # s*_j = argmax_s {clicks_s (v_j - t_s(j))}.
        # - chooses his bid b' for the next round so as to
        # satisfy the following equation:
        # clicks_{s*_j} (v_j - t_{s*_j}(j)) = clicks_{s*_j-1}(v_j - b')
        # (p_x is the price/click in slot x)
        # If s*_j is the top slot, bid the value v_j

        # TODO: Fill this in.

        prev_round = history.round(t-1)

        (slot, min_bid, max_bid) = self.target_slot(t, history, reserve)

        # Compute remaining budget
        self.remaining_budget = self.budget - history.agents_spent[self.id]

        clicks = prev_round.clicks
        norm = max(clicks)
        pos = map(lambda c: float(c) / norm, clicks)

        if slot == 0:
            bid = self.value
        else:
            balance_value = self.value - ((pos[slot] / pos[slot - 1]) * (self.value - min_bid))
            bid = min(self.value, balance_value)

        # Calculate approximate per-round, per-click budget
        budget_per_round = self.remaining_budget/(self.TOTAL_NUM_ROUNDS - t)
        budget_per_click = budget_per_round/(clicks[slot])

        # print("Computed a budget per click of {} and currently have bid {}.\n".format(budget_per_click, bid))
        # print("High alpha is {}\n".format(self.high_alpha))

        # Always bid below high_alpha * per_round remaining price, i.e. in case self.balance_value < remaining
        if bid > self.high_alpha * budget_per_click:
            bid = self.high_alpha * budget_per_click
        # elif bid < self.low_alpha * budget_per_click:
        #     bid = self.low_alpha * budget_per_click

        # GO OUT WITH A BANG: estimate if this bid will be your last, based on previous
        # number of clicks in a slot. If it is, bid your value while you're still eligible
        if self.remaining_budget - (bid * clicks[slot]) <= 0:
            bid = self.value

        # print("Agent {} has {} budget remaining.\n".format(self.id, self.remaining_budget))
        return bid

    def __repr__(self):
        return "%s(id=%d, value=%d)" % (
            self.__class__.__name__, self.id, self.value)


