import hashlib
import json
import time


class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest()


class HospitalChain:
    def __init__(self):
        self.chain = []
    def create_genesis_block(self):
        return Block(0, time.time(), "Genesis Block - Sistem Başlangıcı", "0")
    def create_new_block(self, data, last_block_hash, last_index):
        new_index = last_index + 1
        new_timestamp = time.time()

        new_block = Block(
            index=new_index,
            timestamp=new_timestamp,
            data=data,
            previous_hash=last_block_hash
        )
        return new_block

    @staticmethod
    def is_chain_valid(chain_data):
        for i in range(1, len(chain_data)):
            current = chain_data[i]
            previous = chain_data[i - 1]
            recalculated_hash = Block(
                current['index'],
                current['timestamp'],
                current['data'],
                current['previous_hash']
            ).calculate_hash()
            if current['hash'] != recalculated_hash:
                return False, f"Blok {current['index']} verisi bozulmuş!"
            if current['previous_hash'] != previous['hash']:
                return False, f"Blok {current['index']} önceki blokla eşleşmiyor!"
        return True, "Zincir Sağlam."