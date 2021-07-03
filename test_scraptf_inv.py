import time
import requests
import steam
from steam.abc import SteamID
from urllib.parse import quote
import json



class MyClient(steam.Client):
    async def on_ready(self):  # on_events in a subclassed client don't need the @client.event decorator
        print("------------")
        print("Logged in as")
        print("Username:", self.user)
        print("ID:", self.user.id64)
        print("Friends:", len(self.user.friends))
        print("------------")
        #user = await SteamID.from_url("https://steamcommunity.com/id/tf2scrap36")
        #user = user.id64
        #user = await scrapy.fetch_user(76561198121097365)
        #self.inventory = await user.inventory(steam.STEAM)
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

scrapy = MyClient()
scrapy.run("metal079", "pablo145965", shared_secret="vaOhCJKJzWiu3oTRUbG+cCo5eOk=")

print("hello world")

