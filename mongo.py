from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
# uri = "mongodb+srv://alok94:alok9@cluster0.llir4qw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
from dotenv import load_dotenv
import os
load_dotenv()

uri = os.getenv("MONGO_URL")

# def connect_to_mongodb(host='localhost', port=27017):
#     """
#     Connect to MongoDB server.
    
#     Args:
#         host (str): MongoDB server host (default: 'localhost').
#         port (int): MongoDB server port (default: 27017).
    
#     Returns:
#         MongoClient: Connected MongoDB client.
#     """
#     client = MongoClient(host, port)
#     return client

def connect_to_atlas():
    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))

    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        return client
    except Exception as e:
        print(e)


def insert_one(db, collection_name, document):
    """
    Insert a single document into a collection.
    
    Args:
        db (Database): MongoDB database.
        collection_name (str): Name of the collection.
        document (dict): Document to be inserted.
    
    Returns:
        InsertOneResult: Result of the insert operation.
    """
    collection = db[collection_name]
    result = collection.insert_one(document)
    return result

def insert_many(db, collection_name, documents):
    """
    Insert multiple documents into a collection.
    
    Args:
        db (Database): MongoDB database.
        collection_name (str): Name of the collection.
        documents (list): List of documents to be inserted.
    
    Returns:
        InsertManyResult: Result of the insert operation.
    """
    collection = db[collection_name]
    result = collection.insert_many(documents)
    return result

def find_one(db, collection_name, query=None):
    """
    Find a single document from a collection.
    
    Args:
        db (Database): MongoDB database.
        collection_name (str): Name of the collection.
        query (dict): Query to filter the documents (default: None).
    
    Returns:
        dict: First document matching the query.
    """
    collection = db[collection_name]
    result = collection.find_one(query)
    return result

def find_many(db, collection_name, query=None, projection=None, limit=0):
    """
    Find multiple documents from a collection.
    
    Args:
        db (Database): MongoDB database.
        collection_name (str): Name of the collection.
        query (dict): Query to filter the documents (default: None).
        projection (dict): Projection to include/exclude fields (default: None).
        limit (int): Maximum number of documents to return (default: 0).
    
    Returns:
        Cursor: Cursor to the documents matching the query.
    """
    collection = db[collection_name]
    result = collection.find(query, projection).limit(limit)
    return result

def update_one(db, collection_name, query, update):
    """
    Update a single document in a collection.
    
    Args:
        db (Database): MongoDB database.
        collection_name (str): Name of the collection.
        query (dict): Query to select the document to update.
        update (dict): Update operations to apply to the document.
    
    Returns:
        UpdateResult: Result of the update operation.
    """
    collection = db[collection_name]
    result = collection.update_one(query, update)
    return result

def delete_one(db, collection_name, query):
    """
    Delete a single document from a collection.
    
    Args:
        db (Database): MongoDB database.
        collection_name (str): Name of the collection.
        query (dict): Query to select the document to delete.
    
    Returns:
        DeleteResult: Result of the delete operation.
    """
    collection = db[collection_name]
    result = collection.delete_one(query)
    return result

