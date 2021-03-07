from bs4 import BeautifulSoup # Used for website scraping
import browser_cookie3 as bc # Used for cookie access
import requests # Gets webpages
import pandas as pd # csv file reading
from selenium import webdriver # Potential use for buying cards from scrap.tf
import time
from steampy.client import SteamClient
import pickle
import chromedriver_binary

def OrganizeCardData(cards): # Organizes cards in list in format CARDTITLE, CARDPRICE(in refined), CARDGAMENAME
    organizedCards = [[]]
    for card in range(len(cards)):
        #print(cards[card])
        # Organize titles
        index1 = cards[card].rfind('data-title="') + 12
        index2 = cards[card].rfind('" style=')
        cardTitle = cards[card][index1:index2]

        # Organize price
        index1 = cards[card].rfind('data-item-value="') + 17
        index2 = cards[card].rfind('" data-slot="')
        cardPrice = cards[card][index1:index2]

        # Organize Game Name
        index1 = cards[card].rfind('refined&lt;br/&gt;&lt;br/&gt;') + 29
        index2 = cards[card].rfind('&lt;br/&gt;" data-defindex=') - 13 # 13 is for 'trading card'
        cardGameName = cards[card][index1:index2]

        # Organize Card image
        index1 = cards[card].rfind('background-image:url(') + 21 
        index2 = cards[card].rfind('</div>') - 4
        cardImageURL = cards[card][index1:index2]

        # Organize Card ID
        index1 = cards[card].rfind('data-id="') + 9
        index2 = cards[card].rfind('" data-item-value') 
        cardID = cards[card][index1:index2]

        organizedCards[card].append(cardTitle)
        organizedCards[card].append(cardPrice)
        organizedCards[card].append(cardGameName)
        organizedCards[card].append(cardID)
        #organizedCards[card].append(cardImageURL)
        organizedCards.append([])
    organizedCards.pop()
    return organizedCards

def getKeyPrice(): # Returns current key price as float based on steam market price
    url = "https://steamcommunity.com/market/priceoverview/?appid=440&currency=1&market_hash_name=Mann%20Co.%20Supply%20Crate%20Key"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    
    # Organize price
    index1 = soup.text.rfind('"lowest_price":"$') + 17
    index2 = soup.text.rfind('","volume"')
    keyPrice = soup.text[index1:index2]
    keyPrice = float(keyPrice)
    keyPrice = 2.40
    return keyPrice

def getCardPrice(cardGame, cardExel): # Estimates the card price (in USD) based on the csv file, RETURNS card price in USD (float)
    try:
        nameIndex = cardExel.loc[cardExel['Game'] == cardGame].index[0] # Get index of the row where the game is located
    except:
        return 0.0
    cardPrice = cardExel["Card Avg"][nameIndex] # Get the actual price from the correct column using the row index from above
    return float(cardPrice)

def calculateFee(realPrice): # Calculates how much the steam market listing fee is, RETURNS fee (float)
    steamTransactionFee = round(realPrice *.05, 2)
    if steamTransactionFee < 0.01:
        steamTransactionFee = 0.01
    gameSpecificFee = round(realPrice *.1, 2)
    if gameSpecificFee < 0.01:
        gameSpecificFee = 0.01
    fee = steamTransactionFee + gameSpecificFee
    return fee

def calculateProfit(marketCardPrice, fee, cardPriceInScrap): # Estimates the profit based on the estimated steam market price, current key price, RETURNS profit(float, 2)
    oneScrapRealPrice = (keyPrice / 51) / 9
    realCardPrice = oneScrapRealPrice * cardPriceInScrap
    profit = (marketCardPrice - fee) - realCardPrice
    return round(profit, 2) 

def selectCardsScrapTF(): # Opens webpage with selenium and selects all the cards
    chrome_options  = webdriver.ChromeOptions() 
    #chrome_options.add_argument("user-data-dir=Default") #Path to your chrome profile
    #chrome_options.add_argument("user-data-dir=C:\\Users\\Pablo\\AppData\\Local\\Google\\Chrome\\User Data\\Default") #Path to your chrome profile
    #chrome_options.add_argument("user-data-dir=C:\\Users\\Pablo\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 1") #Path to your chrome profile
    #chrome_options.add_argument("--user-data-dir=Profile 1")
    chrome_options.add_argument('--lang=en_US') 
    chrome_options .add_argument("--disable-gpu")
    chrome_options .add_argument("--no-sandbox")
    #chrome_options.headless = True
    w = webdriver.Chrome(options=chrome_options)

    driver = w
    cookies = pickle.load(open("cookies.pkl", "rb"))
    driver.get("https://scrap.tf/cards/36")
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get("https://scrap.tf/cards/36")
    #pickle.dump( driver.get_cookies() , open("cookies.pkl","wb"))

    elem = driver.find_element_by_id('category-0')
    elem2 = elem.find_element_by_tag_name('div')
    elem3 = elem.find_element_by_tag_name('div')

    # Select the cards using selenium
    estimatedProfit = 0
    selectedCards = 0
    for card in range(10):
        if sortedCards[card][4] < 0.05:
            continue
        selectedCards += 1
        cardHtml = elem.find_element_by_xpath("//*[@data-id='" + sortedCards[card][3]  +   "']")
        driver.execute_script("""arguments[0].setAttribute('class', 'item hoverable quality6 steamCard app753 selected-item')""", cardHtml)
        estimatedProfit += sortedCards[card][4]

    # Check if we selected no cards
    if(selectedCards == 0):
        print("Could not find any cards that fufiled min profit")
        print("Exiting..")
        exit()

    print("DONE!")
    print("Estimated profit: " + str(round(estimatedProfit, 2)))

    # Press submit button
    time.sleep(3)
    python_button = driver.find_elements_by_xpath("//*[@data-original-title='Pay with metal and keys automatically' and @id='trade-btn']")[0]
    python_button.click()
    print("Pressed submit button")

    # accept trade
    waitTime = 0
    params = {'key': '7E0353421C674E0ACC5BADB7A74F9272'}
    while True:
        print("Waiting on trade...")
        time.sleep(10)
        waitTime += 1
        TradeOffers =  steam_client.get_trade_offers(True)
        if TradeOffers['response']['trade_offers_received']:
            break
        if waitTime == 30:
            print("Timed out waiting for trade")
            exit()
    tradeOfferId = TradeOffers['response']['trade_offers_received'][0]['tradeofferid']
    waitTime = 0
    while waitTime < 36:
        print("Attempting to accept trade...")
        time.sleep(5)
        waitTime += 1
        try:
            response = steam_client.accept_trade_offer(tradeOfferId)
        except:
            pass
        print("Accepted Trade!")
        exit()
    print("Trade Done!")

def save_cookies(requests_cookiejar, filename):
    with open(filename, 'wb') as f:
        pickle.dump(requests_cookiejar, f)

def load_cookies(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

# Login to steam
#steam_client = SteamClient('7E0353421C674E0ACC5BADB7A74F9272')
#steam_client.login('metal079', 'pablo145965', 'Steamguard.txt')

# get raw data of scrap.tf card page
session  = requests.session()
url = "https://scrap.tf/cards/36"
keyPrice = getKeyPrice()
print("Current Key Price: " + str(keyPrice))
page = requests.get(url, cookies = load_cookies("request_cookies"))
soup = BeautifulSoup(page.text, 'html.parser')
print(soup)
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

cardExel = pd.read_csv(r'STC_set_data.csv') # Read csv file with card prices
for card in cards: # calculate profit
    try:
        avgPrice = getCardPrice(card[2], cardExel)
    except:
        break
    fee = calculateFee(avgPrice)
    profit = calculateProfit(avgPrice, fee, float(card[1]))
    card.append(profit)
sortedCards = sorted(cards, key = lambda l:l[4]) # Sorts card list by most profitable
for card in sortedCards:
    print(card)

sortedCards.reverse()
selectCardsScrapTF()

# Create the Window
#window = sg.Window('Enter a number example', layout)
#event, values = window.read()
#window.close()

