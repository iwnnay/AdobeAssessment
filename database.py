import json
import os
from typing import List, Dict, Optional

from models import Campaign


DB_PATH = os.path.join(os.getcwd(), "database.json")


class Database:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _read(self) -> List[Dict]:
        with open(self.path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def _write(self, data: List[Dict]):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def next_id(self) -> int:
        data = self._read()
        return (max([row.get("id", 0) for row in data]) + 1) if data else 1

    def add(self, campaign: Campaign) -> Campaign:
        data = self._read()
        data.append(json.loads(campaign.json()))
        self._write(data)
        return campaign

    def update(self, campaign: Campaign):
        data = self._read()
        for i, row in enumerate(data):
            if row.get("id") == campaign.id:
                data[i] = json.loads(campaign.json())
                self._write(data)
                return
        raise KeyError(f"Campaign {campaign.id} not found")

    def get(self, id_: int) -> Optional[Campaign]:
        data = self._read()
        for row in data:
            if row.get("id") == id_:
                return Campaign(**row)
        return None

    def all(self) -> List[Campaign]:
        return [Campaign(**row) for row in self._read()]
