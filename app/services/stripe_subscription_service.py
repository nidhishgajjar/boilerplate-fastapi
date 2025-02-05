from typing import Dict, Any
import json
from app.utils.logger import setup_logger
from app.database.user_repository import UserRepository

logger = setup_logger(__name__)

class StripeSubscriptionService:
    def __init__(self):
        self.user_repo = UserRepository()

    async def handle_subscription_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Handle subscription-related webhook events from Stripe
        """
        # Log all events at DEBUG level
        logger.debug(f"Received stripe event: {event_type}")
        logger.debug(f"Event data: {json.dumps(event_data, indent=2)}")

        try:
            # Handle customer events
            if event_type == 'customer.created':
                await self._handle_customer_created(event_data)
            elif event_type == 'checkout.session.completed':
                await self._handle_checkout_completed(event_data)
            # Handle subscription events
            elif event_type == 'customer.subscription.created':
                await self._handle_subscription_created(event_data)
            elif event_type == 'customer.subscription.updated':
                await self._handle_subscription_updated(event_data)
            elif event_type == 'customer.subscription.deleted':
                await self._handle_subscription_deleted(event_data)
            else:
                logger.debug(f"Unhandled event type: {event_type}")
        except Exception as e:
            logger.error(f"Error handling stripe event {event_type}: {e}")
            raise

    async def _handle_checkout_completed(self, session_data: Dict[str, Any]) -> None:
        """Handle checkout.session.completed event"""
        try:
            customer_id = session_data.get('customer')
            customer_email = session_data.get('customer_details', {}).get('email')
            
            if not customer_email:
                logger.error("No email found in checkout session data")
                return
                
            logger.info(f"Processing checkout completion for email: {customer_email}")
            
            # Find user by email
            user = await self.user_repo.get_by_email(customer_email)
            if not user:
                logger.error(f"No user found with email: {customer_email}")
                return
                
            # Update user with stripe customer ID if not already set
            if not user.get('stripe_customer_id'):
                stripe_data = {
                    'stripe_customer_id': customer_id
                }
                updated_user = await self.user_repo.update_stripe_info(user['id'], stripe_data)
                logger.info(f"Updated user {user['id']} with stripe customer ID: {customer_id}")
            
        except Exception as e:
            logger.error(f"Error handling checkout completion: {e}")
            raise

    async def _handle_customer_created(self, customer_data: Dict[str, Any]) -> None:
        """Handle customer.created event"""
        try:
            customer_id = customer_data.get('id')
            customer_email = customer_data.get('email')
            
            if not customer_email:
                logger.error("No email found in customer data")
                return
                
            logger.info(f"Processing customer creation for email: {customer_email}")
            
            # Find user by email
            user = await self.user_repo.get_by_email(customer_email)
            if not user:
                logger.error(f"No user found with email: {customer_email}")
                return
                
            # Update user with stripe customer ID
            stripe_data = {
                'stripe_customer_id': customer_id
            }
            
            updated_user = await self.user_repo.update_stripe_info(user['id'], stripe_data)
            logger.info(f"Updated user {user['id']} with stripe customer ID: {customer_id}")
            
        except Exception as e:
            logger.error(f"Error handling customer creation: {e}")
            raise

    async def _handle_subscription_created(self, subscription_data: Dict[str, Any]) -> None:
        """Handle subscription.created event"""
        try:
            customer_id = subscription_data.get('customer')
            plan = subscription_data.get('plan', {})
            stripe_plan_id = plan.get('id')
            status = subscription_data.get('status')
            
            if not customer_id:
                logger.error("No customer ID found in subscription data")
                return
                
            if not stripe_plan_id:
                logger.error("No plan ID found in subscription data")
                return
                
            logger.info(f"Processing subscription creation for customer: {customer_id}")
            
            # Find user by stripe customer ID
            user = await self.user_repo.get_by_stripe_customer_id(customer_id)
            if not user:
                logger.error(f"No user found with stripe customer ID: {customer_id}")
                return
                
            # Update user subscription status
            stripe_data = {
                'is_subscribed': True,
                'stripe_plan_id': stripe_plan_id
            }
            
            updated_user = await self.user_repo.update_stripe_info(user['id'], stripe_data)
            logger.info(f"Updated user {user['id']} subscription status and plan: {stripe_plan_id}")
            
        except Exception as e:
            logger.error(f"Error handling subscription creation: {e}")
            raise

    async def _handle_subscription_updated(self, subscription_data: Dict[str, Any]) -> None:
        """Handle subscription updated event"""
        try:
            customer_id = subscription_data.get('customer')
            plan = subscription_data.get('plan', {})
            stripe_plan_id = plan.get('id')
            status = subscription_data.get('status')
            
            if not customer_id:
                logger.error("No customer ID found in subscription data")
                return
            
            # Find user by stripe customer ID
            user = await self.user_repo.get_by_stripe_customer_id(customer_id)
            if not user:
                logger.error(f"No user found with stripe customer ID: {customer_id}")
                return
            
            # Update subscription information
            stripe_data = {
                'stripe_plan_id': stripe_plan_id,
                'is_subscribed': status in ['active', 'trialing']
            }
            
            updated_user = await self.user_repo.update_stripe_info(user['id'], stripe_data)
            logger.info(f"Updated user {user['id']} subscription: active={status in ['active', 'trialing']}, plan={stripe_plan_id}")
            
        except Exception as e:
            logger.error(f"Error handling subscription update: {e}")
            raise

    async def _handle_subscription_deleted(self, subscription_data: Dict[str, Any]) -> None:
        """Handle subscription deleted event"""
        try:
            customer_id = subscription_data.get('customer')
            
            if not customer_id:
                logger.error("No customer ID found in subscription data")
                return
            
            # Find user by stripe customer ID
            user = await self.user_repo.get_by_stripe_customer_id(customer_id)
            if not user:
                logger.error(f"No user found with stripe customer ID: {customer_id}")
                return
            
            # Update subscription status
            stripe_data = {
                'is_subscribed': False
            }
            
            updated_user = await self.user_repo.update_stripe_info(user['id'], stripe_data)
            logger.info(f"Marked subscription as inactive for user: {user['id']}")
            
        except Exception as e:
            logger.error(f"Error handling subscription deletion: {e}")
            raise 