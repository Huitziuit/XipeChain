from hashlib import sha256
from os import system
import time
from pymongo import MongoClient

# Conexión a MongoDB
Mongo_URI = 'mongodb://localhost'
client = MongoClient(Mongo_URI)
db = client['BC_H']
bd_blockchain = db['blockchain']


class Block:
    def __init__(self, data) -> None:
        self.index = str(self.getPrevious_index()+1)                # num of block
        self.previous_hash_block = self.getPrevious_hash()          # previous hash block
        self.timestamp = time.time()                                # date 
        self.data = data                                            # payload
        self.pW = 0                                                 # nounce proof of work
        self.hash = self.hashGenerate()                             # hash block

    def hashGenerate(self):
        content_block = "DATA: " + self.data + " & PREVIOUS HASH: " + self.previous_hash_block + " & PW: " + str(self.pW) + " & timestamp: " + str(self.timestamp)
        return sha256(content_block.encode()).hexdigest()

    def getPrevious_hash(self):
        ultimo_registro = bd_blockchain.find().sort('_id', -1).limit(5)

        if bd_blockchain.count_documents({}) > 0:
            # Si hay registros, obtener el valor del último registro y su 'index'
            ultimo_registro = ultimo_registro[0]
            return str(ultimo_registro['hash'])
        else:
            return "0" * 64
        
    def getPrevious_index(self):
        ultimo_registro = bd_blockchain.find().sort('_id', -1).limit(5)

        if bd_blockchain.count_documents({}) > 0:
            # Si hay registros, obtener el valor del último registro y su 'index'
            ultimo_registro = ultimo_registro[0]
            return int(ultimo_registro['index'])
        else:
            return 0
        
class Blockchain:
    difficulty = 2

    def __init__(self) -> None:
        #Para la parte visual
        self.hashesd = []
        self.bestHash = "0"
        self.bestScore= 0
        self.count = 0

    def add(self, block):
        bd_blockchain.insert_one({
            "index": block.index,
            "previous_hash_block": block.previous_hash_block,
            "timestamp": block.timestamp,
            "data": block.data,         #checksum in DB
            "pW": block.pW,
            "hash": block.hash
        })

    def mine(self, block):
        last_block = bd_blockchain.find().sort('_id', -1).limit(5)
        
        if bd_blockchain.count_documents({}) > 0:
            last_block = last_block[0]
            if self.blockChainValidation(20, str(last_block['index'])):
                pause = input('---- CORRUPT BLOCKS PREVENTED MINING ----')
                return False
            else:
                pause = input('---- SUCCESSFULLY VERIFIED BLOCKS ----')
        while True:
            if block.hash[:self.difficulty] == "7" * self.difficulty:  
                self.add(block)
                pause = input("OKEY, BLOCK HASH "+ block.hash)
                break
            else:
                
                self.visualConsole(block)
                
                block.pW += 1
                block.hash = block.hashGenerate()
        return True

    def blockChainValidation(self, count_limit_blocks, block_init_validation_index):
        current_block= bd_blockchain.find_one({'index':block_init_validation_index})
        previous_block= bd_blockchain.find_one({'index':str(int(block_init_validation_index)-1)})
        

        flag_error_hashes=False
        
        if int(current_block['index']) < count_limit_blocks-1:
            count_limit_blocks = int(current_block['index'])-1

        for i in range(count_limit_blocks):
            if previous_block['hash'] != current_block['previous_hash_block']:
                flag_error_hashes = True
                print(f"ERROR: The value of the previous hash in block {current_block['index']} is different from the hash generated in block {previous_block['index']}")
                break
            
            content_block = "DATA: " + current_block['data'] + " & PREVIOUS HASH: " + current_block['previous_hash_block'] + " & PW: " + str(current_block['pW']) + " & timestamp: " + str(current_block['timestamp'])
            current_block_hash = sha256(content_block.encode()).hexdigest()
            if current_block_hash != current_block['hash']:
                flag_error_hashes = True
                print(f"ERROR: The hash in block {current_block['index']}, does not match the information of the block content")
                break
            print(f'block {current_block['index']} corrupted = {flag_error_hashes}')
            current_block = previous_block
            previous_block = bd_blockchain.find_one({'index':str(int(current_block['index'])-1)})

        #genesis block
        content_block = "DATA: " + current_block['data'] + " & PREVIOUS HASH: " + current_block['previous_hash_block'] + " & PW: " + str(current_block['pW']) + " & timestamp: " + str(current_block['timestamp'])
        current_block_hash = sha256(content_block.encode()).hexdigest()
        if current_block_hash != current_block['hash']:
            flag_error_hashes = True
            print(f"ERROR: The hash in block {current_block['index']}, does not match the information of the block content")
            
        print(f'block {current_block['index']} corrupted = {flag_error_hashes}')
          
        return flag_error_hashes
    
    
    def visualConsole(self, block):
        self.hashesd.append(str(block.hash))
        score = 0;
        for character in block.hash:
            if character=="7":
                score+=1
            else:
                break;
        if score >= self.bestScore:
            self.bestScore = score
            self.bestHash=block.hash
                
        self.count += 1
        if self.count > 10:
            print("\n\nUndermining the transaction:\n" + " ".join(block.data) + "\n\n")
            for i in range(10):
                print("HASH: " + self.hashesd[i])
            print("\nValor of pW "+ str(block.pW))
            self.hashesd.clear()
            self.count = 0
        
            if self.bestHash!="0":
                print("\nBEST HASH -> "+self.bestHash)
            
            time.sleep(0.05)
            system("cls")
        
    def getBlocks(self,registers):
        lastReg = bd_blockchain.find().sort([("_id", -1)]).limit(registers)
        return lastReg
                    

blockchain = Blockchain()
meta_data_db_hash = db.command({'dbhash': 1, 'collections': 'blockchain'})
md5_db = meta_data_db_hash['md5']
print(md5_db)

#print(blockchain.blockChainValidation(20,'3'))
print("""                ..ooo.
             .888888888.
             88"P""T"T888 8o
         o8o 8.8"8 88o."8o 8o
        88 . o88o8 8 88."8 88P"o
       88 o8 88 oo.8 888 8 888 88
       88 88 88o888" 88"  o888 88
       88."8o."T88P.88". 88888 88
       888."888."88P".o8 8888 888                     AGRO - BLOCKCHAIN
       "888o"8888oo8888 o888 o8P"          
        "8888.""888P"P.888".88P                       By Erick HUitziuit Morales
         "88888ooo  888P".o888
           ""8P"".oooooo8888P
  .oo888ooo.    8888NICK8P8
o88888"888"88o.  "8888"".88   .oo888oo..
 8888" "88 88888.       88".o88888888"888.
 "8888o.""o 88"88o.    o8".888"888"88 "88P
  T888C.oo. "8."8"8   o8"o888 o88" ".=888"
   88888888o "8 8 8  .8 .8"88 8"".o888o8P
    "8888C.o8o  8 8  8" 8 o" ...o***8888
      *88888888 * 8 .8  8   88888888888"
        "8888888o  .8o=" o8o..o(8oo88"
            "888" 88"    888888888""
                o8P       "888***
               o88
             oo888""")

input("")
system("cls")
notExit = True
while notExit:
    try:

        option = int(input("1: for mine \n2: for show Blocks\n3: for exit\n"))
    except:
        option = 0
    if option == 1:
        myData = input("BLOCK DATA -> ")
        userBlock = Block(myData)
        blockchain.mine(userBlock)
        #pause = input("OKEY, BLOCK HASH "+ userBlock.hash)
        system("cls")
    elif option == 2:
        regs = blockchain.getBlocks(20)
        for reg in regs:
            print(reg["data"])
        pause = input("")
        system("cls")

    else:
        notExit = 0