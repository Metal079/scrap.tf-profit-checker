from os import wait
from bs4 import BeautifulSoup # Used for website scraping
import browser_cookie3 as bc # Used for cookie access
import requests # Gets webpages
#import urllib.request as requests
import pandas as pd # csv file reading
from selenium import webdriver # Potential use for buying cards from scrap.tf
import time
from steampy.client import SteamClient
import pickle
import urllib.parse
import chromedriver_binary
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from requests_futures.sessions import FuturesSession
import cfscrape

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
    oneScrapRealPrice = (keyPrice / 52) / 9
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
    # makes list of top 20 most profitable cards to potentially buy
    x = 0
    top20 = []
    for index, card in enumerate(mostProfitable):
        if index > 20:
            break
        else:
            top20.append(card)
            x += 1

    # Chrome webdriver stuff
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
    driver = webdriver.Chrome(options=chrome_options)

    # Load page and cookies
    cookies = pickle.load(open("/home/ubuntu/scrap.tf-profit-checker/cookies.pkl", "rb"))
    driver.get("https://scrap.tf/cards/36")
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get("https://scrap.tf/cards/36")
    #pickle.dump( driver.get_cookies() , open("cookies.pkl","wb")) # Dumps cookies

    # Try to find the html thing, no idea why it fails sometimes.
    try:
        elem = driver.find_element_by_id('category-0')
    except:
        print("driver.find_element_by_id('category-0') ERROR, Will skip this loop")
        return 0.0

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

    # Check if we selected no cards and return if we didnt
    if(selectedCards == 0):
        print("Could not find any cards that fufiled min profit")
        print("Exiting..")
        return 0.0

    # We are buying cards so estimate profit and paste date
    t = time.localtime()
    current_time = time.strftime("%D:%H:%M:%S", t)
    print("DONE!: " + current_time)
    print("Estimated profit: " + str(round(estimatedProfit, 2)))

    # Login to steam if needed
    if steam_client.is_session_alive() == False:
        try:
            steam_client.login('metal079', 'pablo145965', '/home/ubuntu/scrap.tf-profit-checker/Steamguard.txt')
        except:
            print("TOO MANY LOGINS, will cooldown a bit")
            time.sleep(3600)
            return 0.0

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
            try:
                steam_client.login('metal079', 'pablo145965', '/home/ubuntu/scrap.tf-profit-checker/Steamguard.txt')
            except:
                print("TOO MANY LOGINS, will cooldown a bit")
                time.sleep(3600)
                return 0.0
        try:
            TradeOffers =  steam_client.get_trade_offers(True)
        except:
            print("Some error getting trade offers")
            return 0.0
        if TradeOffers['response']['trade_offers_received']:
            tradeOfferId = TradeOffers['response']['trade_offers_received'][0]['tradeofferid']
            print("Attempting to accept trade...")
            try:
                response = steam_client.accept_trade_offer(tradeOfferId)
                print("Accepted Trade!")
                break
            except:
                pass
        if waitTime == 15:
            print("Timed out waiting for trade")
            break
    driver.quit()
    return estimatedProfit

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


#steam_client = SteamClient('7E0353421C674E0ACC5BADB7A74F9272')
#steam_client.login('metal079', 'pablo145965', '/home/ubuntu/scrap.tf-profit-checker/Steamguard.txt')
total_profit = 0.0
while(True):
    # get raw data of scrap.tf card page
    #session  = requests.session()
    url = "https://scrap.tf/cards/36"
    keyPrice = getKeyPrice()
    print("Current Key Price: " + str(keyPrice))

    # Organize cards into a string list called cards
    scraper = cfscrape.create_scraper() 
    rawCards = []
    for i in range(0, 10):
        page = scraper.get(url, cookies = load_cookies("/home/ubuntu/scrap.tf-profit-checker/request_cookies"))
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
        except:
            break
        fee = calculateFee(avgPrice)
        profit = calculateProfit(avgPrice, fee, float(card[1]))
        card.append(profit)
    sortedCards = sorted(cards, key = lambda l:l[4]) # Sorts card list by most profitable


    #time_start = time.time()
    
    # Checking actual price of top 30 cards using steamCards website
    headers = {
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://www.google.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8" 
    }
    sortedCards.reverse()
    mostProfitable = []
    for index in range(0,30):
        try:
            appID = getAppID(sortedCards[index][2], cardExel)
            if index > 1 and sortedCards[index][2] != sortedCards[index - 1][2] and appID != None:
                URL_base = "https://www.steamcardexchange.net/index.php?gamepage-appid-"
                URL_full = URL_base + appID
                page = requests.get(URL_full, headers=headers)
                soup = BeautifulSoup(page.text, 'html.parser')
            avgPrice = getSpecificPrice(sortedCards[index][0], appID, soup)
        except:
            break
        fee = calculateFee(avgPrice)
        profit = calculateProfit(avgPrice, fee, float(card[1]))

        mostProfitable.append(sortedCards[index])
        mostProfitable[index][4] = profit
    mostProfitable = sorted(mostProfitable, key = lambda l:l[4]) # Sorts card list by most profitable
    '''
    headers = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
}
    sortedCards.reverse()
    mostProfitable = []
    session = FuturesSession(max_workers=1)
    futures = []
    appIDs = []
    for index in range(0,30):
        try:
            appID = getAppID(sortedCards[index][2], cardExel)
            appIDs.append(appID)
            if appID != None:
                URL_base = "https://www.steamcardexchange.net/index.php?gamepage-appid-"
                URL_full = URL_base + appID
                future = session.get(URL_full, headers=headers)
                future.index = index
                future.scrapPrice = sortedCards[index][1]
                future.appID = appID
                future.cardName = sortedCards[index][0]
                futures.append(future)
                #time.sleep(0.1)
        except:
            break

    #futures=[session.get(f'https://www.steamcardexchange.net/index.php?gamepage-appid-{appid}') for appid in appIDs]
    for thing, future in enumerate(as_completed(futures)):
        page = future.result()
        soup = BeautifulSoup(page.text, 'html.parser')
        avgPrice = getSpecificPrice(future.cardName, future.appID, soup)
        
        fee = calculateFee(avgPrice)
        profit = calculateProfit(avgPrice, fee, float(future.scrapPrice))

        mostProfitable.append(sortedCards[future.index])
        mostProfitable[thing][4] = profit
    mostProfitable = sorted(mostProfitable, key = lambda l:l[4]) # Sorts card list by most profitable
    '''
    #time_end = time.time()
    #print("Total Time: " + str((time_end - time_start)))
    
    #for index, card in enumerate(mostProfitable):
        #print(str(index) + ': ' + str(card))

    # Select and buy cards
    mostProfitable.reverse()
    total_profit += selectCardsScrapTF()

    print("Done with cycle!\n")
    print("Total profit so far: " + str(total_profit))
    time.sleep(600)