from hashlib import sha256
from os import system
import time
from pymongo import MongoClient
import pymongo

from bson import ObjectId



class Block:
    def __init__(self, data, collection_blockchain) -> None:
        self.collection_blockchain = collection_blockchain
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
        ultimo_registro = self.collection_blockchain.find().sort('_id', -1).limit(5)

        if self.collection_blockchain.count_documents({}) > 0:
            # Si hay registros, obtener el valor del último registro y su 'index'
            ultimo_registro = ultimo_registro[0]
            return str(ultimo_registro['hash'])
        else:
            return "0" * 64
        
    def getPrevious_index(self):
        ultimo_registro = self.collection_blockchain.find().sort('_id', -1).limit(5)

        if self.collection_blockchain.count_documents({}) > 0:
            # Si hay registros, obtener el valor del último registro y su 'index'
            ultimo_registro = ultimo_registro[0]
            return int(ultimo_registro['index'])
        else:
            return 0
        
class Blockchain():
    difficulty = 2

    def __init__(self,db, collection_blockchain, collection_users, collection_products) -> None:
        self.collection_blockchain = collection_blockchain
        self.collection_users = collection_users
        self.collection_products = collection_products
        self.db=db

        #Para la parte visual
        self.hashesd = []
        self.bestHash = "0"
        self.bestScore= 0
        self.count = 0

        # si la DB esta vacia entonces agrega el genesis
        if collection_blockchain.count_documents({}) == 0:
            #screenshot db empty
            md5_db = self.getDBscreenshoot()
            system("cls")
            input(f"Se detecto DB vacia, Creando genesis con semilla -> {md5_db}")
            #Minamos el genesis
            genBlock=Block(md5_db, collection_blockchain)
            self.mine(genBlock)
            system("cls")

    def add(self, block):
        self.collection_blockchain.insert_one({
            "index": block.index,
            "previous_hash_block": block.previous_hash_block,
            "timestamp": block.timestamp,
            "data": block.data,         #checksum in DB
            "pW": block.pW,
            "hash": block.hash
        })

    def mine(self, block):
        last_block = self.collection_blockchain.find().sort('_id', -1).limit(5)
        
        #revisa si la bc esta vacia
        if self.collection_blockchain.count_documents({}) > 0:
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


    def validateWithoutMine(self):
        last_block = self.collection_blockchain.find().sort('_id', -1).limit(5)
        
        #revisa si la bc esta vacia
        if self.collection_blockchain.count_documents({}) > 0:
            last_block = last_block[0]
            if self.blockChainValidation(20, str(last_block['index'])):
                pause = input('---- ERROR -> CORRUPT BLOCKS PREVENTED MINING ----')
                return False
            else:
                pause = input('---- SUCCESSFULLY VERIFIED BLOCKS ----')
                return True

    def blockChainValidation(self, count_limit_blocks, block_init_validation_index):
        current_block= self.collection_blockchain.find_one({'index':block_init_validation_index})
        previous_block= self.collection_blockchain.find_one({'index':str(int(block_init_validation_index)-1)})
        
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
            previous_block = self.collection_blockchain.find_one({'index':str(int(current_block['index'])-1)})

        #ultimo bloque por revisar en el caso de ser el unico es el bloque actual
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
        lastReg = self.collection_blockchain.find().sort([("_id", -1)]).limit(registers)
        return lastReg

    def getDBscreenshoot(self):
        md5ForBD = self.db.command({'dbhash': 1})['collections']['users'] + self.db.command({'dbhash': 1})['collections']['products'] + self.db.command({'dbhash': 1})['collections']['transactions']
        return sha256(md5ForBD.encode()).hexdigest()

    def verifySyncWithDB(self):
        DB_screenshot = self.getDBscreenshoot()
        last_reg = self.collection_blockchain.find_one(sort=[('_id', pymongo.DESCENDING)], limit=1)
        proofBlock = "DATA: " + DB_screenshot + " & PREVIOUS HASH: " + last_reg['previous_hash_block'] + " & PW: " + str(last_reg['pW']) + " & timestamp: " + str(last_reg['timestamp'])
        last_reg_block = "DATA: " + last_reg['data'] + " & PREVIOUS HASH: " + last_reg['previous_hash_block'] + " & PW: " + str(last_reg['pW']) + " & timestamp: " + str(last_reg['timestamp'])

        proofBlock_hash = sha256(proofBlock.encode()).hexdigest()
        last_reg_hash = sha256(last_reg_block.encode()).hexdigest()
        system("cls")
        print(f' - Data in last block:   {last_reg["data"]}')
        print(f' - Data Base Screenchot: {DB_screenshot}')
        print(f" * (data of last block + metadata)->HASH   {last_reg_hash}")
        print(f" * (Data Base Screenchot + metadata)->HASH {proofBlock_hash}")


        if proofBlock_hash != last_reg_hash:
            print('\n ERROR: the blockchain is not synchronized with the database')
            input("")
            system("cls")
            return False
        else:
            print('\nBlockchain synchronized with the database')
            input("")
            return True

class UserActions:
    def __init__(self,db,collection_blockchain,collection_users,collection_products,collection_transactions):
        self.db = db
        self.collection_users = collection_users
        self.collection_blockchain = collection_blockchain
        self.collection_products = collection_products
        self.collection_transactions = collection_transactions

    def validate_email(self, email):
        # Verificar si el correo electrónico ya existe en la colección
        usuario_existente = self.collection_users.find_one({"email": email})
        return usuario_existente

    def reg_user(self, email, password, name):
        # Verificar si el correo electrónico ya está en uso
        if self.validate_email(email):
            print("El correo electrónico ya está en uso.")
            return False

        # Crear un nuevo usuario con la lista de monederos vacía
        new_user = {
            "email": email,
            "password": password,
            "name": name,
            "wallet": []
        }

        # Insertar el nuevo usuario en la colección
        result = self.collection_users.insert_one(new_user)

        # Imprimir el ID del usuario insertado
        print("Usuario registrado con el ID:", result.inserted_id)
        return True

    def reg_transaction(self,id_seller,id_buyer,id_product,value):
        # make transaction
        new_transaction = {
            "id_seller": id_seller,
            "id_buyer": ObjectId(id_buyer),
            "id_product": ObjectId(id_product),
            "purchase_value": value,
            "date_transaction": time.time()
        }

        # Insert new transaction in collection
        result = self.collection_transactions.insert_one(new_transaction)
        print("Transaction register with ID:", result.inserted_id)
        

    def reg_product(self, nameProduct, amountProduct, user_id):
        # Crear un nuevo usuario con la lista de monederos vacía
        new_product = {
            "name": nameProduct,
            "amount_kg": amountProduct
        }

        # Insertar el nuevo producto en la colección
        result = self.collection_products.insert_one(new_product)

        # Imprimir el ID del producto insertado
        print("Producto agregado con el ID:", result.inserted_id)
        product_id = result.inserted_id

        # Actualizar la lista de wallet del usuario
        query = {"_id": user_id}
        update = {"$push": {"wallet": product_id}}
        self.collection_users.update_one(query, update)
        return True

    def login(self, email, password):
        # Verificar las credenciales proporcionadas en la base de datos
        user = self.validate_email(email)
        if user:
            # Verificar la contraseña
            if user["password"] == password:
                print("Inicio de sesión exitoso. Bienvenido, {}!".format(user["name"]))
                self.session_user = user 
                return self.session_user
            else:
                print("Contraseña incorrecta. Por favor, inténtalo de nuevo.")
        else:
            print("El correo electrónico proporcionado no está registrado.")

    def get_user_products(self, user_id):

        user_data = self.collection_users.find_one({'_id': ObjectId(user_id)})

        # Verificar si se encontró el usuario y si tiene la lista de wallet
        if 'wallet' in user_data:
            # Obtener la lista de IDs de productos en la wallet del usuario
            wallet_ids = user_data['wallet']

            # Buscar los documentos de productos correspondientes a los IDs en la wallet
            products = self.collection_products.find({"_id": {"$in": wallet_ids}})

            print("My Wallet:")
            for product in products:
                print(product)

        else:
            print("User dont have products in wallet")
            return None
    
    def product_transaction(self,id_seller, id_buyer, id_product,value_purchase):
        
        # Buscar al vendedor y al comprador por su ID
        seller = self.collection_users.find_one({'_id': ObjectId(id_seller)})
        buyer = self.collection_users.find_one({'_id': ObjectId(id_buyer)})
        
        if seller is None or buyer is None:
            input("No se encontró uno de los usuarios.")
            return False

        # Verificar si el vendedor tiene el producto en su wallet
        if ObjectId(id_product) not in seller['wallet']:
            input("El vendedor no tiene este producto en su wallet.")
            return False
        # Remover el producto de la wallet del vendedor y agregarlo a la del comprador
        self.collection_users.update_one({'_id': ObjectId(id_seller)}, {'$pull': {'wallet': ObjectId(id_product)}})
        self.collection_users.update_one({'_id': ObjectId(id_buyer)}, {'$push': {'wallet': ObjectId(id_product)}})
        
        # load transaction in collection of transactions
        self.reg_transaction(id_seller,id_buyer,id_product,value_purchase)

        input("Transferencia realizada con éxito.")
        return True

    def history_product(self, id_producto):
        print('into history product')
        # Buscar todas las transacciones relacionadas con el producto dado
        transactions = self.collection_transactions.find({"id_product": ObjectId(id_producto)}).sort("date_transaction")
        historial = []
        #print(transactions.next())
        # Iterar sobre cada transacción
        for transaction in transactions:
            print('into for')
            id_vendedor = transaction['id_seller']
            id_comprador = transaction['id_buyer']
            precio_compra = transaction['purchase_value']

            # Obtener nombres del vendedor y comprador
            vendedor = self.collection_users.find_one({"_id": id_vendedor})['name']
            print(f'vendedor {vendedor}')
            comprador = self.collection_users.find_one({"_id": id_comprador})['name']

            # Obtener nombre del producto
            nombre_producto = self.collection_products.find_one({"_id": ObjectId(id_producto)})['name']

            historial.append({
                'Producto': nombre_producto,
                'Vendedor': vendedor,
                'Comprador': comprador,
                'Precio de compra': precio_compra
            })
        
        for step_transaction in historial:
            print(step_transaction)
        return historial


def main():
    # Conection MongoDB
    Mongo_URI = 'mongodb://localhost'
    client = MongoClient(Mongo_URI)
    db = client['BC_H']
    collection_blockchain = db['blockchain']
    collection_users = db['users']
    collection_products = db['products']
    collection_transactions = db['transactions']

    #init blockchain
    blockchain = Blockchain(db,collection_blockchain, collection_users, collection_products)

    #init user actions
    user_act = UserActions(db,collection_blockchain,collection_users, collection_products, collection_transactions)
    md5_db = db.command({'dbhash': 1})['md5']
    print(md5_db)

    print("""
            ..ooo.
         .888888888.
         88"P""T"T888 8o
     o8o 8.8"8 88o."8o 8o
    88 . o88o8 8 88."8 88P"o
    88 o8 88 oo.8 888 8 888 88
    88 88 88o888" 88"  o888 88
    88."8o."T88P.88". 88888 88
    888."888."88P".o8 8888 888                     AGRO - BLOCKCHAIN
    "888o"8888oo8888 o888 o8P"          
     "8888.""888P"P.888".88P                       By Erick Huitziuit Morales García
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
        system("cls")
        try:
            option = int(input("1: for mine \n2: for show Blocks\n3: for exit\n4: for register user\n5: for log in\n"))
        except:
            option = 0
        if option == 1:
            myData = input("BLOCK DATA -> ")
            userBlock = Block(myData, collection_blockchain)
            blockchain.mine(userBlock)
            system("cls")
        elif option == 2:
            regs = blockchain.getBlocks(20)
            for reg in regs:
                print(reg["data"])
            pause = input("")
            system("cls")
        elif option == 3:
            notExit = False
        elif option == 4:
            if(blockchain.verifySyncWithDB() and blockchain.validateWithoutMine()):
                email = input("Email: ")
                password = input("Password: ")
                name = input("Name: ")
                if user_act.reg_user(email, password, name):
                    data_block = blockchain.getDBscreenshoot()#db.command({'dbhash': 1})['collections']['users']
                    new_block=Block(data_block, collection_blockchain)
                    blockchain.mine(new_block)
                    system("cls")
        elif option == 5:
            if(blockchain.verifySyncWithDB()):
                email = input("Email: ")
                password = input("Password: ")
                session_current = user_act.login(email, password) 
                if (session_current):
                    print(session_current)
                    
                    # menu logeado
                    notExitUserMenu = True 
                    while notExitUserMenu:
                        optionUser = input('1: logOut\n2: Create product\n3: Seller product\n4: View my wallet\n5: Track product ')
                        if optionUser == '1':
                            notExitUserMenu = False
                        elif optionUser == '2':
                            if(blockchain.verifySyncWithDB() and blockchain.validateWithoutMine()):
                                nameProduct = input('Name of Product: ')
                                amountProduct = input('Amount in Kg: ')
                                user_act.reg_product(nameProduct,amountProduct,session_current['_id'])
                                #add block
                                data_block = blockchain.getDBscreenshoot()#db.command({'dbhash': 1})['collections']['users']
                                new_block=Block(data_block, collection_blockchain)
                                blockchain.mine(new_block)
                                system("cls")
                        elif optionUser == '3':
                                id_buyer=input('ID Buyer: ')
                                id_product= input('ID Product')
                                purchase_value = input("Purchase value")
                                if user_act.product_transaction(session_current['_id'],id_buyer,id_product,purchase_value):
                                    #add block
                                    data_block = blockchain.getDBscreenshoot()#db.command({'dbhash': 1})['collections']['users']
                                    new_block=Block(data_block, collection_blockchain)
                                    blockchain.mine(new_block)
                                    system("cls")
                        elif optionUser == '4':
                            system("cls")
                            user_act.get_user_products(session_current['_id'])
                            stop=input()
                        elif optionUser == '5':
                            id_track_product = input('ID product: ')
                            user_act.history_product(id_track_product)
                        else:
                            pass

        else:
            print("Invalid option.")

    # Cerrar la conexión a MongoDB
    client.close()

if __name__ == "__main__":
    main()


