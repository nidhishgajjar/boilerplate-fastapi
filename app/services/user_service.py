from typing import Dict, Any
import json
from app.database.user_repository import UserRepository
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class UserService:
    def __init__(self):
        self.user_repo = UserRepository()

    async def extract_user_details(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize user details from Clerk webhook payload"""
        try:
            # Get the primary email from email_addresses array
            email_addresses = user_data.get('email_addresses', [])
            primary_email = next((email['email_address'] for email in email_addresses 
                                if email.get('id') == user_data.get('primary_email_address_id')), None)
            
            # If no primary email found, try to get the first email
            if not primary_email and email_addresses:
                primary_email = email_addresses[0].get('email_address')

            # Get primary phone number
            phone_numbers = user_data.get('phone_numbers', [])
            primary_phone_id = user_data.get('primary_phone_number_id')
            
            # Try to get primary phone first, then fallback to first verified phone
            primary_phone = None
            if primary_phone_id:
                primary_phone = next((phone['phone_number'] for phone in phone_numbers 
                                    if phone.get('id') == primary_phone_id), None)
            if not primary_phone and phone_numbers:
                # Try to get first verified phone number
                primary_phone = next((phone['phone_number'] for phone in phone_numbers 
                                    if phone.get('verification', {}).get('status') == 'verified'), None)
            
            # Extract user data matching our schema
            user_details = {
                'id': user_data.get('id'),
                'email': primary_email,
                'phone': primary_phone,
                'username': user_data.get('username'),
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'full_name': f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
            }
            
            # Remove None values
            user_details = {k: v for k, v in user_details.items() if v is not None}
            
            # Log extracted details at debug level
            logger.debug(f"Extracted user details: {json.dumps(user_details, indent=2)}")
            
            return user_details
        except Exception as e:
            logger.error(f"Error extracting user details: {e}")
            raise

    async def handle_user_event(self, event_type: str, user_details: Dict[str, Any]) -> None:
        """Handle different user-related events"""
        try:
            if event_type == 'user.created':
                await self._handle_user_created(user_details)
            elif event_type == 'user.updated':
                await self._handle_user_updated(user_details)
            elif event_type == 'user.deleted':
                await self._handle_user_deleted(user_details)
            else:
                logger.debug(f"Unhandled user event type: {event_type}")
        except Exception as e:
            logger.error(f"Error handling user event: {e}")
            raise

    async def _handle_user_created(self, user_details: Dict[str, Any]) -> None:
        """Handle user creation"""
        try:
            user_id = user_details.get('id')
            if not user_id:
                raise ValueError("User ID is required for creation")

            # Check if user already exists by ID
            existing_user = await self.user_repo.get_by_id(user_id)
            if existing_user:
                logger.info(f"User already exists with ID: {user_id}")
                return existing_user

            # Create new user
            logger.info(f"Creating new user with ID: {user_id}")
            created_user = await self.user_repo.insert(user_details)
            logger.info(f"User created successfully: {json.dumps(created_user, indent=2)}")
            return created_user
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    async def _handle_user_updated(self, user_details: Dict[str, Any]) -> None:
        """Handle user update"""
        try:
            user_id = user_details.get('id')
            if not user_id:
                raise ValueError("User ID is required for update")

            # Verify user exists before update
            existing_user = await self.user_repo.get_by_id(user_id)
            if not existing_user:
                raise ValueError(f"User not found with ID: {user_id}")

            logger.info(f"Updating user: {user_id}")
            updated_user = await self.user_repo.update(user_id, user_details)
            logger.info(f"User updated successfully: {json.dumps(updated_user, indent=2)}")
            return updated_user
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise

    async def _handle_user_deleted(self, user_details: Dict[str, Any]) -> None:
        """Handle user deletion"""
        try:
            user_id = user_details.get('id')
            if not user_id:
                raise ValueError("User ID is required for deletion")

            # Verify user exists before deletion
            existing_user = await self.user_repo.get_by_id(user_id)
            if not existing_user:
                logger.warning(f"User not found for deletion with ID: {user_id}")
                return

            logger.info(f"Deleting user: {user_id}")
            await self.user_repo.delete(user_id)
            logger.info(f"User deleted successfully: {user_id}")
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            raise 