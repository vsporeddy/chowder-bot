from games.slots import slots
import unittest

class TestSlots(unittest.TestCase):

    test_cases = [
        [1, 2, 3, 4, 5], #no win
        [1, 1, 2, 3, 4], #1 pair
        [1, 1, 1, 2 ,3], #three in a row
        [1, 1, 1, 1, 2], #four in a row
        [1, 1, 1, 1, 1], #five in a row
        [1, 2, 1, 1, 1], #three in a row
        [1, 1, 2, 1, 1], #two pair
        [1, 1, 1, 2, 1], #three in a row
        [1, 1, 1, 1, 2], #four in a row
        [1, 2, 2, 1, 1], #two pair
        [1, 2, 1, 2, 1], #no win
        [1, 2, 1, 1, 2], #1 pair
        [1, 1, 2, 2, 1], #two pair
        [1, 1, 1, 2, 2], #full house
        [1, 2, 2, 2, 1], #three in a row
        [1, 2, 2, 1, 2], #1 pair
        [1, 2, 1, 2, 2], #1 pair
        [1, 1, 2, 2, 2], #full house

    ]
    test_cases_wc = [
        [11, 2, 3, 4, 5], #1 pair
        [1, 2, 3, 4, 11], #1 pair
        [1, 2, 3, 11, 11], #three in a row
        [11, 2, 3, 11, 5], #two pair
        [11, 2, 11, 4, 5], #three in a row
        [11, 11, 3, 4, 5], #three in a row
        [11, 2, 3, 4, 11], #two pair
        [1, 11, 3, 4, 11], #two pair
        [1, 2, 11, 4, 11], #three in a row
        [11, 11, 11, 4, 5], #four in a row
        [11, 11, 3, 11, 5], #four in a row
        [11, 11, 3, 4, 11], #full house
        [11, 11, 3, 11, 11], #five in a row
        [1, 2, 11, 4, 4], #three in a row
    ]

    expected = [
        "**You hate to see that.**",
        "**Not bad, skipper.**",
        "**THREE IN A ROW!**",
        "**FOUR IN A ROW!!**",
        "**FIVE IN A ROW!!!**",
        "**THREE IN A ROW!**",
        "**Two pair. Now we're getting somewhere.**",
        "**THREE IN A ROW!**",
        "**FOUR IN A ROW!!**",
        "**Two pair. Now we're getting somewhere.**",
        "**You hate to see that.**",
        "**Not bad, skipper.**",
        "**Two pair. Now we're getting somewhere.**",
        "**FULL HOUSE!!**",
        "**THREE IN A ROW!**",
        "**Not bad, skipper.**",
        "**Not bad, skipper.**",
        "**FULL HOUSE!!**",
    ]

    expected_wc = [
        "**Not bad, skipper.**",
        "**Not bad, skipper.**",
        "**THREE IN A ROW!**",
        "**Two pair. Now we're getting somewhere.**",
        "**THREE IN A ROW!**",
        "**THREE IN A ROW!**",
        "**Two pair. Now we're getting somewhere.**",
        "**Two pair. Now we're getting somewhere.**",
        "**THREE IN A ROW!**",
        "**FOUR IN A ROW!!**",
        "**FOUR IN A ROW!!**",
        "**FULL HOUSE!!**",
        "**FIVE IN A ROW!!!**",
        "**THREE IN A ROW!**",
    ]

    def test_streaks(self):
        wildcard = 11
        for i in range(len(self.test_cases)):
            rolls = slots.check_slots(self.test_cases[i], wildcard)
            test = slots.get_hand(rolls)[0]
            self.assertEqual(test, self.expected[i])
                # print(f"failed {i}")
                # print(self.test_cases[i], rolls, test)
                # print("Should be " + self.expected[i])
    def test_streaks_wc(self):
        wildcard = 11
        for i in range(len(self.test_cases_wc)):
            rolls = slots.check_slots(self.test_cases_wc[i], wildcard)
            test = slots.get_hand(rolls)[0]
            self.assertEqual(test, self.expected_wc[i])

if __name__ == '__main__':
    unittest.main()
