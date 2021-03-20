from os import wait
from bs4 import BeautifulSoup # Used for website scraping
import browser_cookie3 as bc # Used for cookie access
import requests # Gets webpages
import pandas as pd # csv file reading
from selenium import webdriver # Potential use for buying cards from scrap.tf
import time
from steampy.client import SteamClient
import pickle
import chromedriver_binary
import urllib.parse

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
    #url = "https://steamcommunity.com/market/priceoverview/?appid=440&currency=1&market_hash_name=Mann%20Co.%20Supply%20Crate%20Key"
    #page = requests.get(url)
    #soup = BeautifulSoup(page.text, 'html.parser')
    
    # Organize price
    #index1 = soup.text.rfind('"lowest_price":"$') + 17
    #index2 = soup.text.rfind('","volume"')
    #keyPrice = soup.text[index1:index2]
    #keyPrice = float(keyPrice)
    keyPrice = 2.50
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

def getCardVolume(card, cardExel):
    baseurl = "https://steamcommunity.com/market/search/render/?query=MEDIC&appid="
    appid = "753&start=0&count=100&norender=1"
    url = baseurl + appid
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    # Organize price
    index1 = soup.text.rfind('"lowest_price":"$') + 17
    index2 = soup.text.rfind('","volume"')
    keyPrice = soup.text[index1:index2]
    #keyPrice = float(keyPrice)
    keyPrice = 2.40
    return keyPrice

def selectCardsScrapTF(): # Opens webpage with selenium and selects all the cards
    x = 0
    top20 = []
    for index, card in enumerate(mostProfitable):
        if index > 20:
            break
        else:
            top20.append(card)
            x += 1

    chrome_options  = webdriver.ChromeOptions() 
    #chrome_options.add_argument("user-data-dir=Default") #Path to your chrome profile
    #chrome_options.add_argument("user-data-dir=C:\\Users\\Pablo\\AppData\\Local\\Google\\Chrome\\User Data\\Default") #Path to your chrome profile
    #chrome_options.add_argument("user-data-dir=C:\\Users\\Pablo\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 1") #Path to your chrome profile
    #chrome_options.add_argument("--user-data-dir=Profile 1")
    chrome_options.add_argument('--lang=en_US') 
    chrome_options .add_argument("--disable-gpu")
    chrome_options .add_argument("--no-sandbox")
    chrome_options.add_argument('--log-level=0')
    chrome_options.add_argument('--enable-logging')
    chrome_options.add_argument('--single-process')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--window-size=1280x1696')
    chrome_options.headless = True
    w = webdriver.Chrome(options=chrome_options)

    driver = w
    cookies = pickle.load(open("/home/ubuntu/scrap.tf-profit-checker/cookies.pkl", "rb"))
    driver.get("https://scrap.tf/cards/36")
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get("https://scrap.tf/cards/36")
    #pickle.dump( driver.get_cookies() , open("cookies.pkl","wb"))

    try:
        elem = driver.find_element_by_id('category-0')
    except:
        print("driver.find_element_by_id('category-0') ERROR, Will skip this loop")
        return None

    # Select the cards using selenium
    estimatedProfit = 0
    selectedCards = 0
    for card in top20:
        if card[4] < 0.03:
            continue
        try:
            cardHtml = elem.find_element_by_xpath("//*[@data-id='" + card[3]  +   "']")
        except:
            continue
        print(card)
        selectedCards += 1
        driver.execute_script("""arguments[0].setAttribute('class', 'item hoverable quality6 steamCard app753 selected-item')""", cardHtml)
        estimatedProfit += card[4]

    # Check if we selected no cards
    if(selectedCards == 0):
        print("Could not find any cards that fufiled min profit")
        print("Exiting..")
        return None

    t = time.localtime()
    current_time = time.strftime("%D:%H:%M:%S", t)
    print("DONE!: " + current_time)
    print("Estimated profit: " + str(round(estimatedProfit, 2)))

    # Login to steam if needed
    if steam_client.is_session_alive() == False:
        for i in range(0,3):
            try:
                steam_client.login('metal079', 'pablo145965', '/home/ubuntu/scrap.tf-profit-checker/Steamguard.txt')
            except:
                time.sleep(60)
                continue
            break

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
        time.sleep(30)
        waitTime += 1
        if steam_client.is_session_alive() == False:
            steam_client.login('metal079', 'pablo145965', '/home/ubuntu/scrap.tf-profit-checker/Steamguard.txt')
        TradeOffers =  steam_client.get_trade_offers(True)
        if TradeOffers['response']['trade_offers_received']:
            tradeOfferId = TradeOffers['response']['trade_offers_received'][0]['tradeofferid']
            print("Attempting to accept trade...")
            try:
                response = steam_client.accept_trade_offer(tradeOfferId)
                print("Accepted Trade!")
                break
            except:
                pass
        if waitTime == 10:
            print("Timed out waiting for trade")
            break
    driver.quit()

def getAppID(cardGame, cardExel):
    try:
        nameIndex = cardExel.loc[cardExel['Game'] == cardGame].index[0] # Get index of the row where the game is located
    except:
        return None
    appID = cardExel["AppId"][nameIndex] # Get the appId
    return str(appID)

def getSpecificPrice(cardName, appID, soup):
    if appID == None:
        return 0.0
    try:
        cardName = urllib.parse.quote(cardName)
    except:
        pass

    if soup == None:
        URL_base = "https://www.steamcardexchange.net/index.php?gamepage-appid-"
        URL_full = URL_base + appID
        page = requests.get(URL_full)
        soup = BeautifulSoup(page.text, 'html.parser')
    mydivs = soup.find_all("div", {"class": "element-button"})

    # Organize price
    price = 0
    for thing in mydivs:
        if thing.contents[0].attrs['href'].rfind(cardName) == -1:
            continue
        else:
            price = thing.text
            index = price.rfind('Price:') + 8
            price = price[index:]
            break
    return float(price)

def save_cookies(requests_cookiejar, filename):
    with open(filename, 'wb') as f:
        pickle.dump(requests_cookiejar, f)

def load_cookies(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

steam_client = SteamClient('7E0353421C674E0ACC5BADB7A74F9272')
steam_client.login('metal079', 'pablo145965', '/home/ubuntu/scrap.tf-profit-checker/Steamguard.txt')
while(True):
    # get raw data of scrap.tf card page
    session  = requests.session()
    url = "https://scrap.tf/cards/36"
    keyPrice = getKeyPrice()
    print("Current Key Price: " + str(keyPrice))

    # Organize cards into a string list called cards
    rawCards = []
    for i in range(0, 10):
        page = requests.get(url, cookies = load_cookies("/home/ubuntu/scrap.tf-profit-checker/request_cookies"))
        soup = BeautifulSoup(page.text, 'html.parser')
        cardHTML = soup.find(class_='items-container')
        try:
            for child in cardHTML.children:
                if child == '\n':
                    pass
                else:
                    rawCards.append(str(child))
        except:
            continue
        break
    print("The card list has {} objects".format(len(rawCards)))
    cards = OrganizeCardData(rawCards)

    cardExel = pd.read_csv(r'/home/ubuntu/scrap.tf-profit-checker/STC_set_data.csv') # Read csv file with card prices
    soup = None
    for index, card in enumerate(cards): # calculate profit
        try:
            avgPrice = getCardPrice(card[2], cardExel)
            '''
            appID = getAppID(card[2], cardExel)
            if index > 1 and cards[index][2] != cards[index - 1][2] and appID != None:
                URL_base = "https://www.steamcardexchange.net/index.php?gamepage-appid-"
                URL_full = URL_base + appID
                page = requests.get(URL_full)
                soup = BeautifulSoup(page.text, 'html.parser')
            avgPrice = getSpecificPrice(card[0], appID, soup)
            '''
        except:
            break
        fee = calculateFee(avgPrice)
        profit = calculateProfit(avgPrice, fee, float(card[1]))
        card.append(profit)
    sortedCards = sorted(cards, key = lambda l:l[4]) # Sorts card list by most profitable

    sortedCards.reverse()
    mostProfitable = []
    for index in range(0,30):
        try:
            appID = getAppID(sortedCards[index][2], cardExel)
            if index > 1 and sortedCards[index][2] != sortedCards[index - 1][2] and appID != None:
                URL_base = "https://www.steamcardexchange.net/index.php?gamepage-appid-"
                URL_full = URL_base + appID
                page = requests.get(URL_full)
                soup = BeautifulSoup(page.text, 'html.parser')
            avgPrice = getSpecificPrice(sortedCards[index][0], appID, soup)
        except:
            break
        fee = calculateFee(avgPrice)
        profit = calculateProfit(avgPrice, fee, float(card[1]))

        mostProfitable.append(sortedCards[index])
        mostProfitable[index][4] = profit
    mostProfitable = sorted(mostProfitable, key = lambda l:l[4]) # Sorts card list by most profitable
    
    #for index, card in enumerate(mostProfitable):
        #print(str(index) + ': ' + str(card))

    mostProfitable.reverse()
    selectCardsScrapTF()
    print("Done with cycle!\n")
    time.sleep(1200)