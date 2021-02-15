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
        organizedCards[card].append(cardImageURL)
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

sg.Window(title="scrap.tf scrapper", layout=[[sg.Text(cards[0])]], margins=(100, 50)).read()
