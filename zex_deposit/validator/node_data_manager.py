import json
import os
from pyfrost.network.abstract import DataManager


class NodeDataManager(DataManager):
    def __init__(
        self,
        dkg_keys_file="./zex_deposit/dkg_keys.json",
        nonces_file="./zex_deposit/nonces.json",
    ) -> None:
        super().__init__()
        self.dkg_keys_file = dkg_keys_file
        self.nonces_file = nonces_file

        # Load data from files if they exist
        self.__dkg_keys = self._load_data(self.dkg_keys_file)
        self.__nonces = self._load_data(self.nonces_file)

    def _load_data(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                return json.load(file)
        return {}

    def _save_data(self, file_path, data):
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

    def set_nonce(self, nonce_public: str, nonce_private: str) -> None:
        self.__nonces[nonce_public] = nonce_private
        self._save_data(self.nonces_file, self.__nonces)

    def get_nonce(self, nonce_public: str):
        data = self._load_data(self.nonces_file)
        return data.get(nonce_public)

    def remove_nonce(self, nonce_public: str) -> None:
        self.__nonces = self._load_data(self.nonces_file)
        if nonce_public in self.__nonces:
            del self.__nonces[nonce_public]
            self._save_data(self.nonces_file, self.__nonces)

    def set_key(self, key, value) -> None:
        for dkg_id, dkg_data in list(self.__dkg_keys.items()):
            if dkg_data["key_type"] == value["key_type"]:
                del self.__dkg_keys[dkg_id]
                break
        self.__dkg_keys[key] = value
        self._save_data(self.dkg_keys_file, self.__dkg_keys)

    def get_key(self, key):
        data = self._load_data(self.dkg_keys_file)
        return data.get(key, {})

    def remove_key(self, key):
        self.__dkg_keys = self._load_data(self.dkg_keys_file)
        if key in self.__dkg_keys:
            del self.__dkg_keys[key]
            self._save_data(self.dkg_keys_file, self.__dkg_keys)
