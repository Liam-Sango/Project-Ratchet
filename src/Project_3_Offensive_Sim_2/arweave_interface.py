import requests
import uuid

GATEWAYS = ["https://arweave.net", "https://ar-io.net"]

class MockArweave:
    def __init__(self):
        self.store = {}
    
    #Stores a mock transaction in self.store
    def upload_image(self, image_path):
    
        with open(image_path, 'rb') as file:
            image_data = file.read()
        
            txid = uuid.uuid4().hex
            self.store[txid] = image_data

            return txid
    
    #Returns the stored image from self.store
    def download_image(self, txid):
        if txid in self.store:
            stored_bytes = self.store[txid]
            return stored_bytes
        else:
            raise KeyError ("TXID is not present in self.store")

  
def download_image(txid, gateway=None):
    print("TEMP")

def upload_image(wallet, image_path):
    print("TEMP")
    
    

