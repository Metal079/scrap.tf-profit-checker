import urllib.request
from bs4 import BeautifulSoup
import browser_cookie3 as bc
import requests
import PySimpleGUI as sg
import numpy as np
import string

def OrganizeCardData(cards):
    organizedCards = [[]]
    for card in range(len(cards)):
        #print(cards[card])
        # Organize titles
        index1 = cards[card].rfind('data-title="') + 12
        index2 = cards[card].rfind('" style=')
        cardTitle = cards[card][index1:index2]

        # Organize price
        index1 = cards[card].rfind('data-content="') + 20
        index2 = cards[card].rfind(' refined')
        cardPrice = cards[card][index1:index2]

        # Organize Game Name
        index1 = cards[card].rfind('refined&lt;br/&gt;&lt;br/&gt;') + 29
        index2 = cards[card].rfind('&lt;br/&gt;" data-defindex=')
        cardGameName = cards[card][index1:index2]

        # Organize Card image
        index1 = cards[card].rfind('background-image:url(') + 21
        index2 = cards[card].rfind('</div>') - 4
        cardImageURL = cards[card][index1:index2]

        organizedCards[card].append(cardTitle)
        organizedCards[card].append(cardPrice)
        organizedCards[card].append(cardGameName)
        #organizedCards[card].append(cardImageURL)
        organizedCards.append([])

    return organizedCards

# get raw data
s = requests.session()
url = "https://scrap.tf/cards/36"
cookie = bc.chrome()
page = requests.get(url, cookies=cookie)
soup = BeautifulSoup(page.text, 'html.parser')
cardHTML = soup.find(class_='items-container')

# Orginize cards into a string list called cards
rawCards = []
for child in cardHTML.children:
    if child == '\n':
        pass
    else:
        rawCards.append(str(child))

print("The card list has {} objects".format(len(rawCards)))

cards = OrganizeCardData(rawCards)
'''
layout = [[]]
for card in range(len(cards) - 1):
    layout[card].append(sg.Multiline(str(cards[card][0]), size=(35, 3)))
    layout.append([])
'''

# ------ Column Definition ------ #
column1 = [[sg.Text('Column 1', background_color='lightblue', justification='center', size=(10, 1))],
           [sg.Spin(values=('Spin Box 1', '2', '3'), initial_value='Spin Box 1')],
           [sg.Spin(values=('Spin Box 1', '2', '3'), initial_value='Spin Box 2')],
           [sg.Spin(values=('Spin Box 1', '2', '3'), initial_value='Spin Box 3')]]
layout = [
     [sg.Listbox(values=(cards), size=(150, 20))]]

# Create the Window
window = sg.Window('Enter a number example', layout)
event, values = window.read()
window.close()