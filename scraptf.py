from json.decoder import JSONDecodeError
import time
import json
import pickle
from urllib.parse import quote
from concurrent.futures import thread
import subprocess
import threading
from datetime import datetime
import requests # Gets webpages
from bs4 import BeautifulSoup # Used for website scraping
from selenium import webdriver # Potential use for buying cards from scrap.tf
#import steam
#from steam.abc import SteamID
import update_cards

from steampy.client import SteamClient

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
        cardTitle = cardTitle.replace('&amp;', '&')
        cardTitle = cardTitle.replace('&gt;', '>')
        cardTitle = cardTitle.replace('&it;', '<')

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
    keyPrice = 2.30
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
        if index > 19:
            break
        else:
            top20.append(card)
            x += 1

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
        if card[4] < 0.02:
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

    # Login to steam if needed
    try:
        if steam_client.is_session_alive() == False:
            try:
                steam_client.login('metal079', 'pablo145965', '/home/pi/scrap.tf-profit-checker/Steamguard.txt')
            except:
                print("TOO MANY LOGINS, will cooldown a bit")
                driver.quit()
                return 0.0
    except:
        steam_client.login('metal079', 'pablo145965', '/home/pi/scrap.tf-profit-checker/Steamguard.txt')

    # Press submit button
    python_button = driver.find_elements_by_xpath("//*[@data-original-title='Pay with metal and keys automatically' and @id='trade-btn']")[0]
    try:
        python_button.click()
    except:
        print("Button press error, will skip loop")
        return 0.0
    print("Pressed submit button")

    # accept trade
    waitTime = 0
    while True:
        print("Waiting on trade...")
        time.sleep(30)
        waitTime += 1
        if steam_client.is_session_alive() == False:
            try:
                steam_client.login('metal079', 'pablo145965', '/home/pi/scrap.tf-profit-checker/Steamguard.txt')
            except:
                print("TOO MANY LOGINS, will cooldown a bit")
                driver.quit()
                time.sleep(3600)
                return 0.0
        try:
            TradeOffers =  steam_client.get_trade_offers(True)
        except:
            print("Some error getting trade offers")
            driver.quit()
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
            driver.quit()
            return 0.0
    
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

def getMarketHashName(cardName, hash_number):
    name_hash = quote(cardName)
    name_hash = name_hash.replace('/', '-')
    return hash_number + "-" + name_hash

def getSpecificPrice(card, mostProfitableList, price_list): # Gets current price of a card
    global kill_threads
    cardName = card[0]
    hash_number = card[2]
    market_hash_name = getMarketHashName(cardName, hash_number)
    if market_hash_name in price_list.keys():
        current_lowest_price = float(price_list[market_hash_name]['price'])
    else:
        with lock:
            if kill_threads:
                exit()
            try:
                URL_base = "https://steamcommunity.com/market/priceoverview/?appid=753&market_hash_name="
                URL_full = URL_base + market_hash_name
                page = requests.get(URL_full)
                time.sleep(10)
                if page.status_code != 200:
                    print(f"ERROR CODE {page.status_code}")
                    with open("/home/pi/scrap.tf-profit-checker/thread_debug_log.txt", "a", encoding="utf-8") as file_in:
                        file_in.write(f"ERROR CODE {page.status_code};")
                        file_in.write(" card: " + cardName + ";")
                        file_in.write(" appID: " + card[2] + ";")
                        file_in.write(" URL: " + URL_full)
                        file_in.write("\n")
                        file_in.write("\n")
                    return

                json_page = json.loads(page.content)
                if 'lowest_price' in json_page:
                    current_lowest_price = float(json_page['lowest_price'][1:])
                else:
                    current_lowest_price = 0.0

                with open("/home/pi/scrap.tf-profit-checker/price_list.txt", 'a', encoding="utf-8") as file_in:
                    file_in.write('{' + str(current_lowest_price) + ';')
                    file_in.write(cardName + ';')
                    file_in.write(market_hash_name + ';')
                    file_in.write(datetime.today().strftime('%Y-%m-%d') + '}')
                    file_in.write('\n')
                    file_in.write('\n')

            except IndexError:
                current_lowest_price = 0.0

            # No market_hash_name found
            except KeyError:
                current_lowest_price = 0.0
            
            except JSONDecodeError:
                current_lowest_price = 0.0
        
    fee = calculateFee(current_lowest_price)
    profit = calculateProfit(current_lowest_price, fee, float(card[1]))

    mostProfitableList.append(card)
    index = mostProfitable.index(card)
    mostProfitableList[index].append(profit)

def save_cookies(requests_cookiejar, filename):
    with open(filename, 'wb') as f:
        pickle.dump(requests_cookiejar, f)

def load_cookies(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

# load card data from text file and save to dictionary
def load_price_list(price_list):
    with open(price_list, 'r', encoding="utf-8") as file_in:
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

            if market_hash_name.find('-') == -1:
                market_hash_name = getMarketHashName(card_name, market_hash_name)

            card_info = {"price": price,
                        "card_name": card_name,
                        "market_hash_name": market_hash_name,
                        "last_updated": last_updated,}
            
            lines[market_hash_name] = card_info
    
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

def update_inventory(inventory):
    for item in scrapy.inventory.items:
        if item in inventory:
            continue
        else:
            with open("scrapy_inventory.txt", 'a', encoding="utf-8") as file_in:
                # Write card name and internal names
                file_in.write('{Card_name: ' + item.display_name + '; ')
                file_in.write("Internal_name: " + item.tags[1]['internal_name'][4:] + '}')
                file_in.write('\n')
                file_in.write('\n')

# Initial login to steam
total_profit = 0.0 # Initial profit is 0
#subprocess.Popen(['python3', 'test_scraptf_inv.py'])
steam_client = SteamClient('7E0353421C674E0ACC5BADB7A74F9272')
steam_client.login(r'metal079', r'pablo145965', r'/home/pi/scrap.tf-profit-checker/Steamguard.txt')
while(True):
    price_list = load_price_list("/home/pi/scrap.tf-profit-checker/price_list.txt")

    # get raw data of scrap.tf card page
    url = "https://scrap.tf/cards/36"
    keyPrice = getKeyPrice()
    print("Current Key Price: " + str(keyPrice))

    # load page and get html info
    chrome_options  = webdriver.ChromeOptions()
    chrome_options.headless = True
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--window-size=1280x1696')
    chrome_options.add_argument("start-maximized")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36")
    driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', options=chrome_options)
    #driver = webdriver.Chrome(options=chrome_options)
    cookies = load_cookies("/home/pi/scrap.tf-profit-checker/cookies.pkl")
    driver.get("https://scrap.tf/")
    #pickle.dump( driver.get_cookies() , open("yorkie_cookies.pkl","wb")) # Dumps cookies
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get("https://scrap.tf/cards/36")
    time.sleep(20)
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
        driver.quit()
        update_cards.update_price_list()

    print("The card list has {} objects".format(len(rawCards)))
    cards = OrganizeCardData(rawCards)

    # Create threads that check current price of cards using steam api
    mostProfitable = []
    time_start = time.time()
    threads = []
    lock = threading.Lock()
    kill_threads = False
    for index, card in enumerate(cards):
        price_request = threading.Thread(target=getSpecificPrice, args=(card, mostProfitable, price_list))
        price_request.start()
        threads.append(price_request)
    for thread in threads:
        time_end = time.time()
        if time_end - time_start > 300: # Timeout after 5 mins
            kill_threads = True
        thread.join(timeout=60.0)
    mostProfitable = sorted(mostProfitable, key = lambda l:l[4]) # Sorts card list by most profitable

    # Prints time taken to get current price of cards
    time_end = time.time()
    print("Total Time: " + str((time_end - time_start)))
    
    # Print list of eligible cards to buy
    for index, card in enumerate(mostProfitable):
        if card[4] >= 0.02:
            print(str(index) + ': ' + str(card))
    

    # Select and buy cards
    mostProfitable.reverse()
    total_profit += selectCardsScrapTF(driver)

    print("Done with cycle!")
    print("Total profit so far: " + str(total_profit) + '\n')
    #subprocess.call(['python3', 'update_cards.py'])
    update_cards.update_price_list()