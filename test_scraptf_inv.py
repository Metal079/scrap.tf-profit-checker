import time
import requests
import steam
from steam.abc import SteamID
from urllib.parse import quote
import json

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
        if item.name in inventory.keys():
            continue
        else:
            with open("scrapy_inventory.txt", 'a', encoding="utf-8") as file_in:
                # Write card name and internal namesd
                file_in.write('{Card_name: ' + item.display_name + '; ')
                file_in.write("Internal_name: " + item.tags[1]['internal_name'][4:] + '}')
                file_in.write('\n')
                file_in.write('\n')

class MyClient(steam.Client):
    async def on_ready(self):  # on_events in a subclassed client don't need the @client.event decorator
        print("------------")
        print("Logged in as")
        print("Username:", self.user)
        print("ID:", self.user.id64)
        print("Friends:", len(self.user.friends))
        print("------------")

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
        print("Accepted Trade!")

#inventory = load_inventory('scrapy_inventory.txt')
scrapy = MyClient()
scrapy.run("metal079", "pablo145965", shared_secret="vaOhCJKJzWiu3oTRUbG+cCo5eOk=")
#update_inventory(inventory)

print("hello world")

