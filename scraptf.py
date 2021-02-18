import urllib.request
from bs4 import BeautifulSoup
import browser_cookie3 as bc
from numpy import average
import requests
import PySimpleGUI as sg
import pandas as pd

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
        index2 = cards[card].rfind('&lt;br/&gt;" data-defindex=') - 13 # 13 is for 'trading card'
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
        #print(cardGameName)
    organizedCards.pop()
    return organizedCards

def getKeyPrice():
    url = "https://steamcommunity.com/market/priceoverview/?appid=440&currency=1&market_hash_name=Mann%20Co.%20Supply%20Crate%20Key"
    page = requests.get(url, cookies=cookie)
    soup = BeautifulSoup(page.text, 'html.parser')
    
    # Organize price
    index1 = soup.text.rfind('"lowest_price":"$') + 17
    index2 = soup.text.rfind('","volume"')
    keyPrice = soup.text[index1:index2]
    keyPrice = float(keyPrice)
    return keyPrice

def getCardPrice(cardGame):
    cardExel = pd.read_csv(r'STC_set_data.csv') # Read csv file with card prices

    try:
        nameIndex = cardExel.loc[cardExel['Game'] == cardGame].index[0] # Get index of the row where the game is located
    except:
        return 0.0
    cardPrice = cardExel["Card Avg"][nameIndex] # Get the actual price from the correct column using the row index from above
    return float(cardPrice)

def calculateFee(realPrice):
    steamTransactionFee = round(realPrice *.05, 2)
    if steamTransactionFee < 0.01:
        steamTransactionFee = 0.01
    gameSpecificFee = round(realPrice *.05, 2)
    if gameSpecificFee < 0.01:
        gameSpecificFee = 0.01
    fee = steamTransactionFee + gameSpecificFee
    return fee

def calculateProfit(realPrice, fee, refPrice):
    oneRefBaseline = keyPrice / 51
    refPrice = oneRefBaseline * refPrice
    profit = (realPrice - fee) - refPrice
    return round(profit, 2) 

# get raw data
s = requests.session()
url = "https://scrap.tf/cards/36"
cookie = bc.chrome()
keyPrice = getKeyPrice()
print("Current Key Price: " + str(keyPrice))
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
avgPrice = getCardPrice("Team Fortress 2")
fee = calculateFee(avgPrice)
profit = calculateProfit(avgPrice, fee, 0.44)

'''
for card in cards:
    try:
        avgPrice = getCardPrice(card[2])
    except:
        break
    fee = calculateFee(avgPrice)
    profit = calculateProfit(avgPrice, fee, float(card[1]))
    card.append(profit)
    #print(card[0] + ': ' + str(card[2]) + 'cost ' + card[1] + " ref and sells for " + str(avgPrice) + " on steam market, after fees we make " + str(profit) + " Profit")

sortedCards = sorted(cards, key = lambda l:l[3])

for card in sortedCards:
    print(card)

# Create the Window
#window = sg.Window('Enter a number example', layout)
#event, values = window.read()
#window.close()

