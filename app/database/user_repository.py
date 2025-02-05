from typing import Optional, Dict, Any
from app.utils.logger import setup_logger
from app.database.base_repository import BaseRepository

logger = setup_logger(__name__)

class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__("users")
        
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a user by email (auxiliary method, prefer get_by_id)"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq('email', email)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching user by email: {e}")
            raise Exception(f"Failed to fetch user by email: {str(e)}")
            
    async def get_by_stripe_customer_id(self, stripe_customer_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by their Stripe customer ID"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq('stripe_customer_id', stripe_customer_id)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching user by stripe_customer_id: {e}")
            raise Exception(f"Failed to fetch user by stripe_customer_id: {str(e)}")
            
    async def update_stripe_info(self, user_id: str, stripe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user's stripe-related information"""
        try:
            result = self.supabase.table(self.table_name)\
                .update(stripe_data)\
                .eq('id', user_id)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating user stripe info: {e}")
            raise Exception(f"Failed to update user stripe info: {str(e)}")