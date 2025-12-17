import hashlib
import json
import time


class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data  # Hasta verisi (TC, Tanı, vb.)
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """
        Bloğun içeriğini alır ve SHA-256 formatında şifreler.
        """
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest()


class HospitalChain:
    def __init__(self):
        # Bu liste sadece bellekte tutulur, asıl kayıt DB'de olacak.
        self.chain = []

    def create_genesis_block(self):
        """
        İlk blok (Genesis) manuel oluşturulur.
        """
        return Block(0, time.time(), "Genesis Block - Sistem Başlangıcı", "0")

    def create_new_block(self, data, last_block_hash, last_index):
        """
        Web arayüzünden gelen veriyle yeni blok oluşturur.
        """
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
        """
        Veritabanından çekilen zinciri kontrol eder.
        Veri değiştirilmiş mi diye bakar.
        """
        for i in range(1, len(chain_data)):
            current = chain_data[i]
            previous = chain_data[i - 1]

            # 1. Kontrol: Saklanan Hash ile Hesaplanan Hash tutuyor mu?
            # (Veri değiştirildiyse bu tutmaz)
            # DİKKAT: Block sınıfını yeniden oluşturup hash hesaplıyoruz
            recalculated_hash = Block(
                current['index'],
                current['timestamp'],
                current['data'],
                current['previous_hash']
            ).calculate_hash()

            if current['hash'] != recalculated_hash:
                # Hata buradaydı, tek satırda olduğundan emin ol:
                return False, f"Blok {current['index']} verisi bozulmuş!"

            # 2. Kontrol: Zincir kopuk mu?
            if current['previous_hash'] != previous['hash']:
                # Hata ihtimali olan diğer satır:
                return False, f"Blok {current['index']} önceki blokla eşleşmiyor!"

        return True, "Zincir Sağlam."