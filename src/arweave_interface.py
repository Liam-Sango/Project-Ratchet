import requests
import uuid
import arweave

GATEWAYS = ["https://arweave.net", "https://ar-io.net"]

class MockArweave:
    def __init__(self):
        self.store = {}
        self.wallet_history= {}

    #Stores a mock transaction in self.store
    def upload_image(self, wallet_address, image_path):

        with open(image_path, 'rb') as file:
            image_data = file.read()

            txid = uuid.uuid4().hex
            self.store[txid] = image_data
            
        if wallet_address not in self.wallet_history:
            self.wallet_history[wallet_address] = []

        self.wallet_history[wallet_address].append(txid)
        return txid

    #Returns the stored image from self.store
    def download_image(self, txid):
        if txid in self.store:
            stored_bytes = self.store[txid]
            return stored_bytes
        else:
            raise KeyError("TXID is not present in self.store")
    
    #Returns the transactions of a wallet
    def get_wallet_transactions(self, wallet_address):
        return self.wallet_history.get(wallet_address, []) 
    
    def get_latest_transaction(self, wallet_address):
         history = self.wallet_history.get(wallet_address, [])
         
         if not history:
             return None
         else:
             last_TXID = history[-1]
             return last_TXID
         

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

#Uploads an image to the Arweave network and returns the transaction ID
def upload_image(wallet, image_path):

    #Read our image file as raw bytes
    with open(image_path, 'rb') as file:
        image_data = file.read()

    #Create an Arweave transaction
    transaction = arweave.Transaction(wallet, data=image_data)

    #Create a ContentType tag
    transaction.add_tag("Content-Type", "image/png")

    #Sign the transaction
    transaction.sign()

    #Send the transaction
    transaction.send()

    return transaction.id

#Gets wallet transaction history on arweave
def get_wallet_transactions(wallet_address, gateway=None):
    #Builds our GraphQL query
    query = {
        "query": """
        query {
          transactions(
            owners: ["%s"]
            tags: [{ name: "Content-Type", values: ["image/png"] }]
            first: 100
            sort: HEIGHT_ASC
          ) {
            edges {
              node { id }
            }
          }
        }
        """ % wallet_address
    }

    #If a specific gateway is provided, use only that gateway
    if gateway is not None:
        url = f"{gateway}/graphql"
        response = requests.post(url, json=query, timeout=30)
        response.raise_for_status()
        data = response.json()
        edges = data["data"]["transactions"]["edges"]
        return [edge["node"]["id"] for edge in edges]

    #Otherwise try each gateway in order, falling back on failure
    last_exception = None
    for gateway in GATEWAYS:
        url = f"{gateway}/graphql"
        try:
            response = requests.post(url, json=query, timeout=30)
            response.raise_for_status()
            data = response.json()
            edges = data["data"]["transactions"]["edges"]
            return [edge["node"]["id"] for edge in edges]
        except requests.exceptions.RequestException as e:
            last_exception = e
            continue

    raise last_exception

#Gets the latest transaction from arweave
def get_latest_image_txid(wallet_address, gateway=None):
    txids = get_wallet_transactions(wallet_address, gateway)

    if not txids:
        return None
    else:
        return txids[-1]
