from datetime import datetime
import requests
import json
import threading
import time

def main():
    cards = load_price_list('price_list.txt')
    today = datetime.today().strftime('%Y-%m-%d')
    for card in cards:
        if cards[card]['last_updated'] != today:
            index = cards[card]['index']
            update_card(cards, card, index)
            time.sleep(10)

# load card data from text file and save to dictionary
def load_price_list(price_list):
    with open(price_list) as file_in:
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

            card_info = {"price": price,
                        "card_name": card_name,
                        "market_hash_name": market_hash_name,
                        "last_updated": last_updated,
                        "index": index}
            
            lines[card_name] = card_info
    
    return lines

# Updates cards file with new price and last_updated date
def update_card(cards, card, index):
    market_hash_name = cards[card]['market_hash_name']
    URL_base = "https://steamcommunity.com/market/priceoverview/?appid=753&market_hash_name="
    URL_full = URL_base + market_hash_name
    page = requests.get(URL_full)
    json_page = json.loads(page.content)
    try:
        current_lowest_price = float(json_page['lowest_price'][1:])

    # Returned null due to asking too often, sleep for an hour
    except TypeError:
        time.sleep(3700)
        return

    lock = threading.Lock()
    with lock:
        with open("price_list.txt", 'w', encoding="utf-8") as file_in:
            data[index] = '{' + str(current_lowest_price) + ';'
            data[index] += card + ';'
            data[index] += market_hash_name + ';'
            data[index] += datetime.today().strftime('%Y-%m-%d') + '}'
            data[index] += '\n'
            file_in.writelines(data)

main()