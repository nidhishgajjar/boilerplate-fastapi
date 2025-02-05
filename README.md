# FastAPI Boilerplate with Stripe, Supabase, and Clerk Integration

A production-ready boilerplate for building subscription-based web applications using FastAPI, with Stripe for payments, Supabase for database, and Clerk for authentication.

## Features

- 🔐 **User Management** with Clerk
  - OAuth (Google, etc.)
  - Email/Password
  - User Profile Management
  - Webhook Integration

- 💳 **Stripe Integration**
  - Subscription Management
  - Customer Management
  - Webhook Integration
  - Payment Link Support

- 🗄️ **Database Integration** with Supabase
  - User Data Storage
  - Subscription Tracking
  - Automated Timestamps
  - Efficient Indexing

- 🚀 **Modern Stack**
  - FastAPI for high performance
  - Async/await support
  - Type hints throughout
  - Structured logging

## Prerequisites

- Python 3.8+
- [ngrok](https://ngrok.com/) for webhook testing
- Accounts on:
  - [Stripe](https://stripe.com) (for payments)
  - [Supabase](https://supabase.com) (for database)
  - [Clerk](https://clerk.dev) (for authentication)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Set Up Python Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Supabase Setup

1. Create a new project on [Supabase](https://app.supabase.com)
2. Go to Project Settings > Database to find your connection details
3. In the SQL Editor, run the following schema:

```sql
-- Create users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    username TEXT UNIQUE,
    full_name TEXT,
    first_name TEXT,
    last_name TEXT,
    is_subscribed BOOL NOT NULL DEFAULT FALSE,
    stripe_customer_id TEXT UNIQUE,
    stripe_plan_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Create indexes for frequent queries
CREATE INDEX users_email_idx ON users(email);
CREATE INDEX users_username_idx ON users(username);

-- Add a trigger to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc', NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE
    ON users
    FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();
```

4. Get your Supabase URL and anon key from Project Settings > API

### 4. Stripe Setup

1. Create an account on [Stripe](https://stripe.com)
2. Go to Developers > API keys
3. Get your test Secret key
4. Create a payment link:
   - Go to Payment Links in Stripe Dashboard
   - Create a new payment link
   - Configure your product/price
   - Example: https://buy.stripe.com/test_00gbMje8a9VW6FqbII?prefilled_email=test@test.com
5. Save your payment link URL

### 5. Clerk Setup

1. Create a new application on [Clerk](https://dashboard.clerk.dev)
2. Configure your OAuth providers (Google, etc.)
3. Get your API keys from the dashboard
4. Configure your webhook endpoints (we'll add the URL later)

### 6. Environment Setup

Create a `.env` file in your project root:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
```

### 7. Start the Development Server

```bash
# Start the FastAPI server
uvicorn main:app --reload --port 8000
```

### 8. Set Up ngrok for Webhook Testing

1. Install ngrok if you haven't already:
```bash
# Using Homebrew on macOS
brew install ngrok

# Or download from ngrok.com
```

2. Start ngrok tunnel:
```bash
ngrok http 8000
```

3. Copy your ngrok URL (e.g., https://your-tunnel.ngrok.io)

### 9. Configure Webhooks

#### Stripe Webhooks
1. Go to Stripe Dashboard > Developers > Webhooks
2. Add endpoint: `https://your-tunnel.ngrok.io/webhook/stripe`
3. Select events to listen for:
   - customer.created
   - customer.updated
   - customer.subscription.created
   - customer.subscription.updated
   - customer.subscription.deleted
   - checkout.session.completed
4. Save and get your webhook signing secret
5. Update your `.env` file with the webhook secret

#### Clerk Webhooks
1. Go to Clerk Dashboard > Webhooks
2. Add endpoint: `https://your-tunnel.ngrok.io/webhook/user-profile`
3. Select events:
   - user.created
   - user.updated
   - user.deleted
4. Save the configuration

## Testing the Setup

1. Start your FastAPI server:
```bash
uvicorn main:app --reload --port 8000
```

2. Start ngrok:
```bash
ngrok http 8000
```

3. Test user creation:
   - Sign up a new user through your Clerk integration
   - Check the logs for webhook reception
   - Verify user creation in Supabase

4. Test subscription:
   - Use your Stripe payment link
   - Complete a test purchase
   - Verify the subscription status update in your database

## Project Structure

```
app/
├── services/
│   ├── stripe_subscription_service.py
│   └── user_service.py
├── database/
│   └── base_repository.py
└── utils/
    └── logger.py
main.py
.env
requirements.txt
```

## Key Features Explained

### User Management
- Automatic user creation when users sign up through Clerk
- Profile updates sync to database
- Email change handling
- Phone number management

### Subscription Management
- Customer creation in Stripe
- Subscription status tracking
- Plan changes
- Subscription cancellation

### Database Features
- Automatic timestamp management
- Efficient indexing
- Unique constraint enforcement
- Relationship management

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

MIT License
