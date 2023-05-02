from colorama import Fore, init, Style
from settingsmanager import load_settings
from embeds import now
import embeds
import requests
import os
import logging
import socket
import threading
import helheim

init()
logging.basicConfig(format='%(message)s')
helheim.auth('c59b57f1-e200-4146-96cc-95169533acb3')

def injection(session, response):
    if helheim.isChallenge(session, response):
        return helheim.solve(session, response)
    return response

class Monitor:
    def __init__(self):
        self.settings = load_settings()
        self.settings["api_url"] = "https://api.currys.co.uk/smartphone/api/productsStock/"
        self.settings["fe_url"] = "https://api.currys.co.uk/store/api/products/"
        self.error = False

    def load_pids(self) -> list:
        try:
            with open("tasks.csv", "r+") as file:
                pids = [row.split(",")[1] for row in file]
                if pids[0].upper() == "PID":
                    if len("".join(pids[1:])) == 0:
                        logging.warning(f"{Fore.RED}[JBOT] [{now()}] No PIDS Found!{Style.RESET_ALL}")
                        self.error = True
                    else:
                        return pids[1:]
                else:
                    logging.warning(f"{Fore.RED}[JBOT] [{now()}] PID Column Not Found!{Style.RESET_ALL}")
                    self.error = True
        except FileNotFoundError:
            logging.warning(f"{Fore.RED}[JBOT] [{now()}] tasks.csv Does Not Exist!{Style.RESET_ALL}")
            self.error = True
            

class FrontendMonitor(Monitor):
    def __init__(self):
        super().__init__()
        self.pids = self.load_pids()
        if not self.error:
            self.threads = len(self.pids)
            self.pinged = {pid: {"current": False, "prev": False} for pid in self.pids}
            os.system(f"title Monitoring: {len(self.pids)} PIDS - Mode: Frontend API- Threads: {self.threads}")

    def get_product_data(self, response):
        product_data = response.json()["payload"][0]
        title = product_data["label"]
        img_url = product_data["images"][0]["url"]
        instock = product_data["deliveryOptions"][1]["enabled"]
        price = product_data["price"]["amount"]
        return title, img_url, instock, price

    def monitor_pid(self, scraper, pid: int):
        try:
            response = scraper.get(self.settings["fe_url"] + pid, timeout=self.settings["timeout"])
            title, img_url, instock, price = self.get_product_data(response)
            logging.warning(f"{Fore.CYAN}[{now()}] [CURRYS FE] [{response.status_code}] MONITORING: {pid}{Style.RESET_ALL}")
            if instock:
                self.pinged[pid]["prev"] = self.pinged[pid]["current"]
                if not self.pinged[pid]["prev"]:
                    embed = embeds.FrontendMonitorEmbed(pid, self.settings["webhook"])
                    embed.send_embed(title, img_url, price)
                    self.pinged[pid]["current"] = True
            else:
                self.pinged[pid]["current"] = False
        except (AttributeError, socket.gaierror):
            logging.warning(f"{Fore.RED}[{now()}] [CURRYS FE] [{response.status_code}] FAILED LOADING: {pid}{Style.RESET_ALL}") 
        except KeyError:
            logging.warning(f"{Fore.RED}[{now()}] [CURRYS FE] [{response.status_code}] FAILED PARSING DATA: {pid}{Style.RESET_ALL}")
        except requests.exceptions.RequestException:
            logging.warning(f"{Fore.RED}[{now()}] [CURRYS FE] [{response.status_code}] ERROR SENDING REQUEST: {pid}{Style.RESET_ALL}") 
        except KeyboardInterrupt:
            self.error = True

        
    def monitor_all_pids(self, scraper):
        if not self.error:
            try:
                threads = [threading.Thread(target=self.monitor_pid, args=[scraper, pid]) for pid in self.pids]
                for th in threads:
                    th.start()
                for th in threads:
                    th.join()
            except KeyboardInterrupt:
                self.error = True
                
class APIMonitor(Monitor):
    def __init__(self):
        super().__init__()
        self.pids = self.load_pids()
        if not self.error:
            self.threads = len(self.pids)
            self.stock = {pid: [0,0] for pid in self.pids}
            os.system(f"title Monitoring: {len(self.pids)} PIDS - Mode: API - Threads: {self.threads}")

    def monitor_api(self,scraper, pid: int):
        try:
            response = scraper.get(self.settings["api_url"] + pid, timeout=self.settings["timeout"])
            stock_data = response.json()["payload"][0]
            loaded = stock_data["quantityPhysical"]
            purchasable = stock_data["quantityAvailable"]
            print(loaded, purchasable)
            logging.warning(f"{Fore.CYAN}[{now()}] [CURRYS API] [{response.status_code}] REQUESTING: {pid}{Style.RESET_ALL}")

            if not (purchasable <= 0 or purchasable == self.stock[pid][1]):
                embed = embeds.APIMonitorEmbed(pid, self.settings["webhook"], scraper)
                embed.send_embed(loaded, purchasable)
                self.stock[pid] = [loaded, purchasable]
        except KeyError:
            logging.warning(f"{Fore.RED}[{now()}] [CURRYS API] [{response.status_code}] FAILED PARSING DATA: {pid}{Style.RESET_ALL}")
        except requests.exceptions.RequestException:
            logging.warning(f"{Fore.RED}[{now()}] [CURRYS API] [{response.status_code}] ERROR SENDING REQUEST: {pid}{Style.RESET_ALL}")
            


    def monitor_all_pids(self,scraper):
        if not self.error:
            try:
                threads = [threading.Thread(target=self.monitor_api, args=[scraper,pid]) for pid in self.pids]

                for th in threads:
                    th.start()
                for th in threads:
                    th.join()
            except KeyboardInterrupt:
                self.error = True
