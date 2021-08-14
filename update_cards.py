from datetime import datetime
from typing import OrderedDict
import requests
import json
import time
from urllib.parse import quote


def update_price_list():
    cards = load_price_list('/home/pi/scrap.tf-profit-checker/price_list.txt')
    today = datetime.today().strftime('%Y-%m-%d')
    cards = organize_price_list(cards)
    time_start = time.time()
    for card in cards:
        if card[1]['last_updated'] == today:
            continue
        elif card[1]['price'] == '0.0':
            continue
        else:
            index = card[1]['index']
            update_card(cards, card, index)
            time_end = time.time()
            time.sleep(90)
            if time_end - time_start > 2700:
                print("Update card program has exited")
                exit()

def getMarketHashName(cardName, hash_number):
    name_hash = quote(cardName)
    name_hash = name_hash.replace('/', '-')
    return hash_number + "-" + name_hash

# load card data from text file and save to dictionary
def load_price_list(price_list):
    with open(price_list, 'r', encoding="utf-8") as file_in:
        global data
        data = file_in.readlines()
        lines = {}
        for index, line in enumerate(data):
            if line == '\n':
                continue
            elif line == '{PRICE;CARD_NAME;MARKET_HASH_NAME;LAST_UPDATED}\n':
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
                        "last_updated": last_updated,
                        "index": index}
            
            lines[market_hash_name] = card_info
    
    return lines

# Reorders price_list to have most out of date cards listed first.
# TODO
def organize_price_list(cards):
    sorted_cards = sorted(cards.items(), key=lambda k_v: k_v[1]['last_updated'])
    return sorted_cards


# Updates cards file with new price and last_updated date
def update_card(cards, card, index):
    market_hash_name = card[1]['market_hash_name']
    URL_base = "https://steamcommunity.com/market/priceoverview/?appid=753&market_hash_name="
    URL_full = URL_base + market_hash_name
    page = requests.get(URL_full)
    
    # Returned null due to asking too often, sleep for an hour
    if page.status_code == 500 or page.status_code == 502:
        print(f"ERROR CODE {page.status_code}, unknown error")
        print(URL_full)
        print(card[1]['card_name'])
        print(card[1]['market_hash_name'])
        print('\n')
        return

    elif page.status_code != 200:
        print(f"ERROR CODE {page.status_code}")
        exit()

    json_page = json.loads(page.content)
    try:
        current_lowest_price = float(json_page['lowest_price'][1:])
    except KeyError:
        print("Empty json")
        return

    with open("/home/pi/scrap.tf-profit-checker/price_list.txt", 'w', encoding="utf-8") as file_in:
        data[index] = '{' + str(current_lowest_price) + ';'
        data[index] += card[1]['card_name'] + ';'
        data[index] += market_hash_name + ';'
        data[index] += datetime.today().strftime('%Y-%m-%d') + '}'
        data[index] += '\n'
        file_in.writelines(data)
        print("Updated " + card[0] + " from " + card[1]['last_updated'] + " to " + datetime.today().strftime('%Y-%m-%d'))

