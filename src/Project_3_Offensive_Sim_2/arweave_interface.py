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

#Downloads an image from an Arweave gateway, falling back through GATEWAYS on failure
def download_image(txid, gateway=None):
    
    #If a specific gateway is provided, use only that gateway
    if gateway is not None:
        url = f"{gateway}/{txid}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content

    #Otherwise try each gateway in order, falling back on failure
    last_exception = None
    for gateway in GATEWAYS:
        url = f"{gateway}/{txid}"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            last_exception = e
            continue

    raise last_exception

def upload_image(wallet, image_path):
    print("TEMP")

    
    

