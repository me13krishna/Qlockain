import hashlib
import json
import time
from datetime import datetime


class Block:
    def __init__(self, index, data, previous_hash, difficulty=3):
        self.index = index
        self.timestamp = time.time()
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.difficulty = difficulty
        self.hash = self.mine_block()

    def compute_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self):
        prefix = "0" * self.difficulty
        while True:
            computed = self.compute_hash()
            if computed.startswith(prefix):
                return computed
            self.nonce += 1

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "timestamp_readable": datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash,
            "difficulty": self.difficulty
        }


class Blockchain:
    def __init__(self, difficulty=3):
        self.difficulty = difficulty
        self.chain = []
        self._create_genesis_block()

    def _create_genesis_block(self):
        genesis = Block(
            index=0,
            data={
                "type": "GENESIS",
                "message": "Qlockain Genesis Block — Identity Vault Initialized",
                "creator": "Qlockain System"
            },
            previous_hash="0" * 64,
            difficulty=self.difficulty
        )
        self.chain.append(genesis)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, data):
        new_block = Block(
            index=len(self.chain),
            data=data,
            previous_hash=self.last_block.hash,
            difficulty=self.difficulty
        )
        self.chain.append(new_block)
        return new_block

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Recompute and compare hash
            saved_hash = current.hash
            current.hash = current.compute_hash()
            if saved_hash != current.hash:
                current.hash = saved_hash
                return False, i, "Hash mismatch — block tampered"

            if current.previous_hash != previous.hash:
                return False, i, "Chain broken — previous hash mismatch"

            if not current.hash.startswith("0" * self.difficulty):
                return False, i, "Proof-of-work invalid"

        return True, -1, "Chain is valid"

    def find_block_by_hash(self, identity_hash):
        for block in self.chain:
            if isinstance(block.data, dict):
                if block.data.get("identity_hash") == identity_hash:
                    return block
                if block.data.get("document_hash") == identity_hash:
                    return block
        return None

    def get_all_blocks(self):
        return [block.to_dict() for block in self.chain]

    def get_chain_stats(self):
        return {
            "total_blocks": len(self.chain),
            "difficulty": self.difficulty,
            "last_block_hash": self.last_block.hash,
            "genesis_hash": self.chain[0].hash,
            "is_valid": self.is_chain_valid()[0]
        }


# Global singleton blockchain instance
_blockchain_instance = None


def get_blockchain():
    global _blockchain_instance
    if _blockchain_instance is None:
        _blockchain_instance = Blockchain(difficulty=3)
    return _blockchain_instance


def add_identity_to_chain(user_id, username, identity_hash):
    bc = get_blockchain()
    data = {
        "type": "IDENTITY_REGISTRATION",
        "user_id": user_id,
        "username": username,
        "identity_hash": identity_hash,
        "action": "NEW_IDENTITY"
    }
    block = bc.add_block(data)
    return block


def add_document_to_chain(user_id, filename, document_hash):
    bc = get_blockchain()
    data = {
        "type": "DOCUMENT_UPLOAD",
        "user_id": user_id,
        "filename": filename,
        "document_hash": document_hash,
        "action": "DOCUMENT_STORED"
    }
    block = bc.add_block(data)
    return block


def add_verification_to_chain(user_id, result, identity_hash):
    bc = get_blockchain()
    data = {
        "type": "VERIFICATION_LOG",
        "user_id": user_id,
        "identity_hash": identity_hash,
        "result": result,
        "action": "IDENTITY_VERIFIED"
    }
    block = bc.add_block(data)
    return block


def verify_identity_on_chain(identity_hash):
    bc = get_blockchain()
    block = bc.find_block_by_hash(identity_hash)
    if block is None:
        return "INVALID", None
    valid, _, msg = bc.is_chain_valid()
    if not valid:
        return "TAMPERED", block.to_dict()
    return "VERIFIED", block.to_dict()
