import random
from ff_bot.nouns import NOUNS
from ff_bot.verbs import VERBS
from ff_bot.adjectives import ADJECTIVES


def throw_salt(name):
    noun0 = str.lower(NOUNS[random.randint(0, len(NOUNS)-1)])
    adjective0 = str.lower(ADJECTIVES[random.randint(0, len(ADJECTIVES)-1)])
    verb0 = str.lower(VERBS[random.randint(0, len(VERBS)-1)])

    salt0 = name + " is a " + adjective0 + " " + noun0 + "."
    salt1 = name + " likes to " + verb0 + " a " + adjective0 + " " + noun0 + " before breakfast."
    salt2 = name + " smells like a " + adjective0 + " " + noun0 + ", but worse."
    salt3 = name + " looks like a " + adjective0 + " " + noun0 + "."
    salt4 = "i have never seen a " + noun0 + " as " + adjective0 + " as " + name + "."
    salt5 = name + " is the biggest " + noun0 + " that ever lived!"
    salt6 = "you can't spell " + name + " without " + noun0 + "."
    salt7 = "hey " + name + ", go " + verb0 + " a " + noun0 + "!"
    salts = [salt0, salt1, salt2, salt3, salt4, salt5, salt6,salt7]

    return salts[random.randint(0, len(salts)-1)]
