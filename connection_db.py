import pymongo
from bson import ObjectId
from datetime import datetime
from pymongo.errors import DuplicateKeyError
import certifi
ca = certifi.where()

class ConnectionsCollection:
    def __init__(self, connection_string, database_name, collection_name):
        self.client = pymongo.MongoClient(connection_string)
        
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        self.collection.create_index([("ConnectionName", pymongo.ASCENDING)], unique=True)

    def insert_document(self, document):
        document["_id"] = ObjectId()  # Generate a unique ObjectId
        document["LastModifiedDate"] = datetime.now()
        document["LastUpdatedDate"] = datetime.now() # Replace with actual last updated date
        document["CreatedDate"] = datetime.now()
        document["ConnectionDate"] = datetime.now()
        try:
            result = self.collection.insert_one(document)
            return "success"
        except DuplicateKeyError:
            return "DuplicateKey"
        except Exception as e:
            return str(e)
        

    def retrieve_document(self, query):
        return self.collection.find(query)
    
    def retrieve_all_document(self):
        return self.collection.find()
    
    def retrieve_all(self):
        return self.collection.find({}, {"Type": 1, "ConnectionName": 1, "_id": 0})
    
    def retrieve_connection_creds(self, connectionName, getgraphname = False):
        print("connectionName:",connectionName)
        query = {
            "ConnectionName":connectionName
        }
        res = self.collection.find_one(query)
        print("result:",res)
        Uri = res["URL"]
        Username = res["Username"]
        password = res["Password"]
        if getgraphname:
            return Uri,Username,password,res["GraphName"]
        else:
            return Uri,Username,password
    
    def update_document_newkey(self, connection_name, new_key, new_value):
        try:
            # Update the document where ConnectionName matches the user input
            result = self.collection.update_one(
                {"ConnectionName": connection_name},
                {"$set": {new_key: new_value}}
            )

            if result.matched_count > 0:
                return {"status": True, "message": "Document updated successfully"}
            else:
                return {"status": False, "message": "Document not found"}

        except Exception as e:
            return {"status": False, "message": f"An error occurred: {str(e)}"}
        
    def update_key_name(dictionary, old_key, new_key):
    # Check if the old key exists in the dictionary
        if old_key in dictionary:
            # Create a new key-value pair with the new key name
            dictionary[new_key] = dictionary.pop(old_key)
            return True  # Indicates successful update
        else:
            return False
    
    def update_document(self,document_id,update_data):
        try:
            # Update the document where _id matches the ObjectId
            update_data.pop("id")
            print(document_id)
            result = self.collection.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": update_data}
            )

            if result.matched_count > 0:
                return {"status": True, "message": "Document updated successfully"}
            else:
                return {"status": False, "message": "Document not found"}

        except Exception as e:
            return {"status": False, "message": f"An error occurred: {str(e)}"}
    
    def insert_document(self, document):
        try:
            document["_id"] = ObjectId()  # Generate a unique ObjectId
            current_time = datetime.now()
            document["LastModifiedDate"] = current_time
            document["LastUpdatedDate"] = current_time  # Replace with actual last updated date
            document["CreatedDate"] = current_time
            document["ConnectionDate"] = current_time

            result = self.collection.insert_one(document)
            return {"status": True, "message": "Document inserted successfully", "_id": str(result.inserted_id)}

        except DuplicateKeyError as e:
            return {"status": False, "message": str(e)}

        except Exception as e:
            return {"status": False, "message": f"An error occurred: {str(e)}"}


    
    def delete_document(self,object_id):
        try:
            # Convert the string object_id to ObjectId
            object_id = ObjectId(object_id)
            
            # Assuming you have a collection named "items" in your MongoDB
            
            
            # Delete the document with the specified ObjectId
            result = self.collection.delete_one({"_id": object_id})
            
            if result.deleted_count > 0:
                return {"status": True, "message": "Document deleted successfully"}
            else:
                return {"status": False, "message": "Document not found"}
        
        except Exception as e:
            return {"status": False, "message": f"An error occurred: {str(e)}"}

    def close_connection(self):
        self.client.close()