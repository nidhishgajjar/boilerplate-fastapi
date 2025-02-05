from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import stripe
import os
from dotenv import load_dotenv
from app.services.stripe_subscription_service import StripeSubscriptionService
from app.utils.logger import setup_logger
from app.services.user_service import UserService
import json
# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logger(__name__)

# Get required environment variables
stripe_key = os.environ.get('STRIPE_SECRET_KEY')
webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

# Validate required environment variables
if not stripe_key:
    raise ValueError("STRIPE_SECRET_KEY environment variable is required")
if not webhook_secret:
    raise ValueError("STRIPE_WEBHOOK_SECRET environment variable is required")

# Configure Stripe
stripe.api_key = stripe_key
endpoint_secret = webhook_secret

logger.info("Stripe configuration loaded successfully")

app = FastAPI()
stripe_service = StripeSubscriptionService()
user_service = UserService()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post('/webhook/stripe')
async def webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not sig_header:
        logger.error("No Stripe signature header found in the request")
        raise HTTPException(status_code=400, detail="No Stripe signature header found")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        logger.debug(f"Webhook secret used: {endpoint_secret[:6]}...")  # Log first 6 chars for debugging
        logger.debug(f"Signature header: {sig_header[:6]}...")  # Log first 6 chars for debugging
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    event_type = event['type']
    event_data = event['data']['object']
    
    # Log all events at DEBUG level
    logger.debug(f"Received webhook event: {event_type}")
    
    # Handle both customer and subscription events
    if event_type.startswith('customer.') or event_type.startswith('checkout.session.'):
        await stripe_service.handle_subscription_event(event_type, event_data)
    else:
        # Log other events at debug level
        logger.debug(f"Unhandled event type: {event_type}")

    return {"status": "success"}




@app.post("/webhook/user-profile")
async def user_created_webhook(request: Request):
    try:
        payload = await request.json()
        
        logger.debug(f"Received webhook payload: {json.dumps(payload, indent=2)}")
        
        event_type = payload.get('type', 'N/A')
        user_data = payload.get('data', {})
        
        if not user_data:
            raise HTTPException(status_code=400, detail="Invalid webhook payload: missing user data")
            
        user_details = await user_service.extract_user_details(user_data)
        
        await user_service.handle_user_event(event_type, user_details)
        
        return {
            "status": "success",
            "event_type": event_type,
            **user_details
        }
    except Exception as e:
        logger.error(f"Error processing user profile webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))





if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
    