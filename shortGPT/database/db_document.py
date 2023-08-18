import threading
from abc import ABC, abstractmethod

import tinydb
import tinymongo as tm


class AbstractDatabaseDocument(ABC):
    @abstractmethod
    def _save(self, key, data):
        """Save the data in the database"""
        pass

    @abstractmethod
    def _get(self, key):
        """Get the data from the database"""
        pass

    @abstractmethod
    def _getId(self):
        """Get the id of the document"""
        pass

    @abstractmethod
    def __str__(self):
        """Return the string representation of the document"""
        pass

    @abstractmethod
    def _delete(self):
        """Delete the document"""
        pass


class TinyMongoClient(tm.TinyMongoClient):
    @property
    def _storage(self):
        return tinydb.storages.JSONStorage


TINY_MONGO_DATABASE = TinyMongoClient("./.database")


class TinyMongoDocument(AbstractDatabaseDocument):
    _lock = threading.Lock()

    def __init__(
        self, db_name: str, collection_name: str, document_id: str, create=False
    ):
        self.collection = TINY_MONGO_DATABASE[db_name][collection_name]
        self.collection_name = collection_name
        self.document_id = document_id
        if not self.exists_internal():
            if create:
                self.collection.insert_one({"_id": document_id})
            else:
                raise Exception(
                    f"The document with id {document_id} in collection {collection_name} of database {db_name} does not exist"
                )

    def exists(self):
        with self._lock:
            return self.exists_internal()

    def exists_internal(self):
        return self.collection.find({"_id": self.document_id}).count() == 1

    def _save(self, data):
        with self._lock:
            self._save_internal(data)

    def _save_internal(self, data):
        print("Lock acquired in _save method")
        try:
            update_data = {"$set": {}}
            for key, value in data.items():
                path_parts = key.split(".")

                if len(path_parts) > 1:
                    root_key = ".".join(path_parts[:-1])
                    last_key = path_parts[-1]
                    current_value = self._internal_get(root_key)
                    if not isinstance(current_value, dict):
                        current_value = {}
                    current_value[last_key] = value
                    update_data["$set"][root_key] = current_value
                else:
                    update_data["$set"][key] = value

            self.collection.update_one({"_id": self.document_id}, update_data)
        except Exception as e:
            print(f"Error saving data: {e}")

    def _get(self, key=None):
        with self._lock:
            return self._internal_get(key)

    def _internal_get(self, key):
        print("Lock acquired in _get method")
        try:
            document = self.collection.find_one({"_id": self.document_id})
            if not key:
                del document["_id"]
                return document
            keys = key.split(".")
            value = document[keys[0]]
            for k in keys[1:]:
                value = value[k]
            return value
        except Exception as e:
            return None

    def _delete(self, key):
        with self._lock:
            self._delete_internal(key)

    def _delete_internal(self, key):
        try:
            self.collection.update_one({"_id": self.document_id}, {"$unset": {key: ""}})
        except Exception as e:
            print(f"Error deleting key '{key}': {e}")

    def _getId(self):
        return self.document_id

    def __str__(self):
        with self._lock:
            return self._str_internal()

    def _str_internal(self):
        document = self.collection.find_one({"_id": self.document_id})
        return str(document)
