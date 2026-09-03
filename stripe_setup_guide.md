# Stripe Setup Guide for Credit Payments

## 1. Create a Stripe account
- Go to https://dashboard.stripe.com/register
- Sign up and complete verification

## 2. Create products and prices
In Stripe Dashboard:
- Go to Product catalog
- Add product: `50 Credits`
- Set price: `$12.00`
- Save the resulting price ID
- Repeat for:
  - `100 Credits` = `$24.00`
  - `200 Credits` = `$48.00`
  - `400 Credits` = `$96.00`

## 3. Copy the price IDs
You will get values like:
- `price_abc123...`
- `price_def456...`

## 4. Add environment variables
Create a `.env` file in the project root based on `.env.example`.

Example:

```bash
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_PRICE_50=price_abc123
STRIPE_PRICE_100=price_def456
STRIPE_PRICE_200=price_ghi789
STRIPE_PRICE_400=price_jkl012
APP_URL=http://localhost:8509
```

## 5. Install dependencies
```bash
pip install -r requirements.txt
```

## 6. Start the app
```bash
streamlit run app.py
```

## 7. Test payment flow
- Login as a member
- Open the Billing page
- Click a package
- Stripe checkout opens
- Use Stripe test card details for testing

## 8. Stripe test card
For test mode use:
- Card number: `4242 4242 4242 4242`
- Expiry: any future date
- CVC: any 3 digits

## 9. Production notes
- Use live Stripe keys for real money
- Keep `STRIPE_SECRET_KEY` secret
- Never expose your secret key in the frontend
- Store users and credits in a database for real production use

## 10. Important security note
Never put raw card numbers in the app, in chat, or in code. Stripe handles card data securely.
