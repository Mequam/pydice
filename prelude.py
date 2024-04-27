"""
this file is inteanded to be included as a prelude to compiler outputs
for the pydice langauge, theres not much in here to run otherwise :)
"""

import pydice

context = pydice.DiceSetParser(only_operations=True)

context.delimiters = []

def get_delimiter():
    if len(context.delimiters) <= 0:
        return " "
    return context.delimiters[-1]

def clean_delimiters():
    if len(context.delimiters) >= 2:
        if context.delimiters[-1] != context.delimiters[-2]:
            print(context.delimiters[-2],end="")

    context.delimiters = context.delimiters[:-1]
