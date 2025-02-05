import os
from supabase import create_client
from supabase.client import Client
from datetime import datetime, UTC
from typing import Optional, Dict, Any, List
from decimal import Decimal
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class BaseRepository:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.supabase: Client = create_client(
            os.environ.get("SUPABASE_URL", ""),
            os.environ.get("SUPABASE_KEY", "")
        )

    def _serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Decimal and other non-JSON-serializable types to appropriate format"""
        serialized = {}
        for key, value in data.items():
            if isinstance(value, Decimal):
                serialized[key] = str(value)  # Convert Decimal to string to preserve precision
            else:
                serialized[key] = value
        return serialized

    async def insert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a record into the table"""
        try:
            # Add timestamps
            now = datetime.now(UTC).isoformat()
            data['created_at'] = now
            data['updated_at'] = now
            
            # Serialize the data
            serialized_data = self._serialize_data(data)
            
            result = self.supabase.table(self.table_name).insert(serialized_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error inserting into {self.table_name}: {e}")
            raise Exception(f"Failed to insert into {self.table_name}: {str(e)}")

    async def update(self, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a record in the table"""
        try:
            update_data = data.copy()
            update_data.pop('id', None)  # Remove id from update data
            update_data.pop('created_at', None)  # Don't update creation time
            update_data['updated_at'] = datetime.now(UTC).isoformat()
            
            # Serialize the data
            serialized_data = self._serialize_data(update_data)
            
            result = self.supabase.table(self.table_name)\
                .update(serialized_data)\
                .eq('id', id)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating {self.table_name}: {e}")
            raise Exception(f"Failed to update {self.table_name}: {str(e)}")

    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a record by ID"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq('id', id)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching from {self.table_name}: {e}")
            raise Exception(f"Failed to fetch from {self.table_name}: {str(e)}")

    async def get_all(self) -> List[Dict[str, Any]]:
        """Base get all method"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching all from {self.table_name}: {e}")
            raise Exception(f"Failed to get all from {self.table_name}: {str(e)}")

    async def delete(self, id: str) -> bool:
        """Base delete method"""
        try:
            result = self.supabase.table(self.table_name)\
                .delete()\
                .eq('id', id)\
                .execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error deleting from {self.table_name}: {e}")
            raise Exception(f"Failed to delete from {self.table_name}: {str(e)}") 