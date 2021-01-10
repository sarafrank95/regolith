from copy import deepcopy
from collections import defaultdict

from regolith.fsclient import FileSystemClient
from regolith.mongoclient import MongoClient


CLIENTS = {
    'mongo': MongoClient,
    'mongodb': MongoClient,
    'fs': FileSystemClient,
    'filesystem': FileSystemClient,
    }


class ClientManager:
    """
    Client wrapper that allows for multiple backend clients to be used in parallel with one chained DB
    """
    def __init__(self, databases, rc):
        self.clients = ()
        for database in databases:
            if not hasattr(database, "backend"):
                #for backwards compatabity, since most people using an FS backend won't have the backend keyword in rc
                database["backend"] = 'filesystem'
            backend_object_type = CLIENTS[database["backend"]]
            #Checks to see if the clients tuple contains a client with the database's backend
            if True not in [isinstance(client, backend_object_type) for client in self.clients]:
                self.clients = self.clients + (CLIENTS[database["backend"]](rc),)
        self.rc = rc
        self.closed = True
        self.chained_db = None
        self.open()
        self._collfiletypes = {}
        self._collexts = {}
        self._yamlinsts = {}

    def __getattribute__(self, item):
        if str(item) is "dbs":
            concatenated_dbs_dict = defaultdict(lambda: defaultdict(dict))
            for client in self.clients:
                concatenated_dbs_dict.update(client.dbs)
            return concatenated_dbs_dict
        else:
            object.__getattribute__(self, item)

    def __getitem__(self, key):
        for client in self.clients:
            if key in client.keys():
                return client[key]

    def open(self):
        """Opens the database connections"""
        for client in self.clients:
            client.open()

    def close(self):
        """Closes the database connections."""
        for client in self.clients:
            client.close()

    def load_database(self, db):
        for client in self.clients:
            if isinstance(client, CLIENTS[db["backend"]]):
                client.load_database(db)

    def import_database(self, db: dict):
        for client in self.clients:
            if isinstance(client, MongoClient):
                client.import_database(db)

    def dump_database(self, db):
        for client in self.clients:
            if isinstance(client, CLIENTS[db["backend"]]):
                client.dump_database(db)

    def keys(self):
        keys = []
        for client in self.clients:
            keys.append(client.keys())
        return keys

    def collection_names(self, dbname, include_system_collections=True):
        """Returns the collaction names for a database."""
        for client in self.clients:
            if dbname in client.keys():
                return client.collection_names(dbname)

    def all_documents(self, collname, copy=True):
        """Returns an iteratable over all documents in a collection."""
        if copy:
            return deepcopy(self.chained_db.get(collname, {})).values()
        return self.chained_db.get(collname, {}).values()

    def insert_one(self, dbname, collname, doc):
        """Inserts one document to a database/collection."""
        for client in self.clients:
            if dbname in client.keys():
                client.insert_one(dbname, collname, doc)

    def insert_many(self, dbname, collname, docs):
        """Inserts many documents into a database/collection."""
        for client in self.clients:
            if dbname in client.keys():
                client.insert_many(dbname, collname, docs)

    def delete_one(self, dbname, collname, doc):
        """Removes a single document from a collection"""
        for client in self.clients:
            if dbname in client.keys():
                client.delete_one(dbname, collname, doc)

    def find_one(self, dbname, collname, filter):
        """Finds the first document matching filter."""
        for client in self.clients:
            if dbname in client.keys():
                return client.find_one(dbname, collname, filter)

    def update_one(self, dbname, collname, filter, update, **kwargs):
        """Updates one document."""
        for client in self.clients:
            if dbname in client.keys():
                client.update_one(dbname, collname, filter, update, **kwargs)

