import time
import json
import pickle
from urllib.parse import quote
from concurrent.futures import thread
import threading
from datetime import datetime
import requests # Gets webpages
from bs4 import BeautifulSoup # Used for website scraping
import pandas as pd # csv file reading
from selenium import webdriver # Potential use for buying cards from scrap.tf
import chromedriver_binary
from proxy_requests import ProxyRequests
import steam
from steam.abc import SteamID


def OrganizeCardData(cards): # Organizes cards in list in format CARDTITLE, CARDPRICE(in refined), CARDGAMENAME
    organizedCards = [[]]
    for card in range(len(cards)):
        #print(cards[card])
        # Organize titles
        index1 = cards[card].rfind('data-title="') 
        index2 = cards[card].rfind('" style=')
        cardTitle = cards[card][index1:index2]
        index1 = cardTitle.rfind('data-title="') + 12
        index2 = cardTitle.rfind('(') - 1
        cardTitle = cardTitle[index1:index2]

        # Organize price
        index1 = cards[card].rfind('data-item-value="') + 17
        index2 = cards[card].rfind('" data-slot="')
        cardPrice = cards[card][index1:index2]

        # Organize Game ID
        index1 = cards[card].rfind('data-title="') + 11
        index2 = cards[card].rfind('" style') # 13 is for 'trading card'
        cardGameName = cards[card][index1:index2]
        index1 = cardGameName.rfind('(') + 1
        index2 = cardGameName.rfind(')')
        cardGameName = cardGameName[index1:index2]

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
    oneScrapRealPrice = (keyPrice / 60) / 9
    realCardPrice = oneScrapRealPrice * cardPriceInScrap
    profit = (marketCardPrice - fee) - realCardPrice
    return round(profit, 2) 

def selectCardsScrapTF(driver): # Opens webpage with selenium and selects all the cards
    # makes list of top 20 most profitable cards to potentially buy
    x = 0
    top20 = []
    for index, card in enumerate(mostProfitable):
        if index > 20:
            break
        else:
            top20.append(card)
            x += 1
    '''
    # Chrome webdriver stuff
    chrome_options  = webdriver.ChromeOptions() 
    #chrome_options.add_argument("user-data-dir=Default") #Path to your chrome profile
    #chrome_options.add_argument("user-data-dir=C:\\Users\\Pablo\\AppData\\Local\\Google\\Chrome\\User Data\\Default") #Path to your chrome profile
    #chrome_options.add_argument("user-data-dir=C:\\Users\\Pablo\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 1") #Path to your chrome profile
    #chrome_options.add_argument("--user-data-dir=Profile 1")
    #chrome_options.add_argument('--lang=en_US') 
    #chrome_options .add_argument("--disable-gpu")
    #chrome_options .add_argument("--no-sandbox")
    #chrome_options.add_argument('--log-level=0')
    #chrome_options.add_argument('--enable-logging')
    #chrome_options.add_argument('--single-process')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--window-size=1280x1696')
    chrome_options.headless = True
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except:
        print("Driver initialization error, will skip loop")
        return 0.0

    # Load page and cookies
    cookies = load_cookies("cookies.pkl")
    driver.get("https://scrap.tf/")
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get("https://scrap.tf/cards/36")
    #pickle.dump( driver.get_cookies() , open("cookies.pkl","wb")) # Dumps cookies
    '''
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
            cardHtml = elem.find_element_by_xpath('//*[@data-id="' + card[3]  +   '"]')
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

    # Press submit button
    python_button = driver.find_elements_by_xpath("//*[@data-original-title='Pay with metal and keys automatically' and @id='trade-btn']")[0]
    try:
        python_button.click()
    except:
        print("Button press error, will skip loop")
        return 0.0
    print("Pressed submit button")
    
    time.sleep(20)
    driver.quit()
    return round(estimatedProfit, 2)

def getAppID(cardGame, cardExel): # Get's AppId of game
    try:
        nameIndex = cardExel.loc[cardExel['Game'] == cardGame].index[0] # Get index of the row where the game is located
    except:
        return None
    appID = cardExel["AppId"][nameIndex] # Get the appId
    return str(appID)

def getSpecificPrice(card, mostProfitableList, price_list): # Gets current price of a card
    cardName = card[0]
    lock = threading.Lock()
    if cardName in price_list:
        current_lowest_price = float(price_list[cardName]['price'])
    else:
        try:
            market_hash_name = scrapy.get_card_hash_name(cardName)
            URL_base = "https://steamcommunity.com/market/priceoverview/?appid=753&market_hash_name="
            URL_full = URL_base + market_hash_name
            page = requests.get(URL_full)
            json_page = json.loads(page.content)
            current_lowest_price = float(json_page['lowest_price'][1:])

            with lock:
                with open("price_list.txt", 'a', encoding="utf-8") as file_in:
                    file_in.write('{' + str(current_lowest_price) + ';')
                    file_in.write(cardName + ';')
                    file_in.write(market_hash_name + ';')
                    file_in.write(datetime.today().strftime('%Y-%m-%d') + '}')
                    file_in.write('\n')
                    file_in.write('\n')

        except IndexError:
            current_lowest_price = 0.0
        
        #Too many requests
        except TypeError: 
            current_lowest_price = 0.0

        except:
            current_lowest_price = 0.0
        
    fee = calculateFee(current_lowest_price)
    profit = calculateProfit(current_lowest_price, fee, float(card[1]))

    with lock:
        mostProfitableList.append(card)
    index = mostProfitable.index(card)
    mostProfitableList[index][4] = profit
    with lock:
        try:
            log.write("card: " + cardName + "---")
            log.write("price: " + str(current_lowest_price) + '---')
            log.write("hash_name: " + market_hash_name + '---')
            log.write("URL: " + URL_full + '---')
            log.write("appID: " + card[2])
            log.write("\n")
        except UnicodeEncodeError:
            return

        except UnboundLocalError:
            return

def save_cookies(requests_cookiejar, filename):
    with open(filename, 'wb') as f:
        pickle.dump(requests_cookiejar, f)

def load_cookies(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

# load card data from text file and save to dictionary
def load_price_list(price_list):
    with open(price_list) as file_in:
        lines = {}
        for line in file_in:
            if line == '\n':
                continue
            index1 = line.find('{') 
            index2 = line.find(';') 
            price = line[index1 + 1:index2]

            index1 = line.find(';', index2) 
            index2 = line.find(';', index1 + 1) 
            card_name = line[index1 + 1:index2]

            index1 = line.find(';', index2) 
            index2 = line.find(';', index1 + 1) 
            market_hash_name = line[index1 + 1:index2]

            index1 = line.find(';', index2) 
            index2 = line.find('}') 
            last_updated = line[index1 + 1:index2]

            card_info = {"price": price,
                        "card_name": card_name,
                        "market_hash_name": market_hash_name,
                        "last_updated": last_updated,}
            
            lines[card_name] = card_info
    
    return lines

def load_inventory(file):
    with open(file, 'r', encoding="utf-8") as file_in:
        lines = {}
        for line in file_in:
            if line == '\n':
                continue
            index1 = line.find('{') 
            index2 = line.find(';') 
            card_name = line[index1 + 12:index2]

            index1 = line.find(';', index2) 
            index2 = line.find(';', index1 + 1) 
            internal_name = line[index1 + 17:index2]

            card_info = {"card_name": card_name,
                        "internal_name": internal_name}
            
            lines[card_name] = card_info
    
    return lines

class MyClient(steam.Client):
    async def connect(self):  # on_events in a subclassed client don't need the @client.event decorator
        print("------------")
        print("Logged in as")
        print("Username:", self.user)
        print("ID:", self.user.id64)
        print("Friends:", len(self.user.friends))
        print("------------")
        user = await SteamID.from_url("https://steamcommunity.com/id/tf2scrap36")
        user = user.id64
        user = await scrapy.fetch_user(76561198121097365)
        self.inventory = await user.inventory(steam.STEAM)
        with open("scrapy_inventory.txt", 'w', encoding="utf-8") as file_in:
            for item in self.inventory.items:
                # Write card name and internal names
                file_in.write('{Card_name: ' + item.display_name + '; ')
                file_in.write("Internal_name: " + item.tags[1]['internal_name'][4:] + '}')
                file_in.write('\n')
                file_in.write('\n')
        print('got inventory')

    # Search inventory of scrapy and return hash_name of provided card
    def get_card_hash_name(self, cardName):
        matches = self.inventory.filter_items(cardName)
        hash_number = matches[0].tags[1]['internal_name']
        hash_number = hash_number[4:]

        hash_name = hash_number + "-" + quote(cardName)
        return hash_name

    async def on_trade_receive(self, trade: "steam.TradeOffer") -> None:
        print(f"Received trade: #{trade.id}")
        print("Trade partner is:", trade.partner)
        print("We would send:", len(trade.items_to_send), "items")
        print("We would receive:", len(trade.items_to_receive), "items")
        await trade.accept()

# Initial login to steam
scrapy = MyClient()
scrapy.run("metalyorkie", "0hBhG2ZtPK4O", ) #shared_secret="vaOhCJKJzWiu3oTRUbG+cCo5eOk=" metal079
total_profit = 0.0 # Initial profit is 0
#inventory = load_inventory('scrapy_inventory')
while(True):
    # get raw data of scrap.tf card page
    url = "https://scrap.tf/cards/36"
    keyPrice = getKeyPrice()
    print("Current Key Price: " + str(keyPrice))

    # load page and get html info
    chrome_options  = webdriver.ChromeOptions() 
    #chrome_options.headless = True
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--window-size=1280x1696')
    driver = webdriver.Chrome(options=chrome_options)
    cookies = load_cookies("cookies.pkl")
    driver.get("https://scrap.tf/")
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get("https://scrap.tf/cards/36")
    time.sleep(10)
    page = driver.page_source
    
    # Organize cards
    rawCards = []
    soup = BeautifulSoup(page, 'html.parser')
    cardHTML = soup.find(class_='items-container')
    try:
        for child in cardHTML.children:
            if child == '\n':
                pass
            else:
                rawCards.append(str(child))
    except:
        print("Error getting cards")
        exit()
    print("The card list has {} objects".format(len(rawCards)))
    cards = OrganizeCardData(rawCards)

    # Estimate card prices based on csv file and order list accordingly.
    cardExel = pd.read_csv(r'STC_set_data.csv') # Read csv file with card prices
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

    # Create new list using only the top priced N cards
    '''
    sortedCards.reverse()
    top30 = []
    if len(sortedCards) < 100: # If we have less than 50 cards retry loop
        continue
    for index in range(0, 100):
        top30.append(sortedCards[index])
    '''

    # Create threads that check current price of cards using steam api
    mostProfitable = []
    time_start = time.time()
    threads = []
    log = open("thread_debug_log.txt", "w")
    log.write("-------")
    log.close()
    log = open("thread_debug_log.txt", "a", encoding="utf-8")
    price_list = load_price_list("price_list.txt")
    for index, card in enumerate(sortedCards):
        price_request = threading.Thread(target=getSpecificPrice, args=(card, mostProfitable, price_list))
        price_request.start()
        threads.append(price_request)
    for thread in threads:
        thread.join(timeout=None)
    log.close()

    mostProfitable = sorted(mostProfitable, key = lambda l:l[4]) # Sorts card list by most profitable

    # Prints time taken to get current price of cards
    time_end = time.time()
    print("Total Time: " + str((time_end - time_start)))
    
    for index, card in enumerate(mostProfitable):
        if card[4] >= 0.0:
            print(str(index) + ': ' + str(card))

    # Select and buy cards
    mostProfitable.reverse()
    total_profit += selectCardsScrapTF(driver)

    print("Done with cycle!\n")
    print("Total profit so far: " + str(total_profit))
    time.sleep(3600)
