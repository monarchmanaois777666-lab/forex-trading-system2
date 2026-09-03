# UmBruM deployment plan

This is the production deployment blueprint for UmBruM.

## Public web launch

The app is a Streamlit web app. The right public deployment path is to host the web app on a public server and keep the payment/access rules identical to the local version.

### Recommended public host

Use Render or Streamlit Cloud.

#### Render
1. Push this repository to GitHub.
2. In Render, create a new Web Service.
3. Connect the repository.
4. Set the build command to:
   pip install -r requirements.txt
5. Set the start command to:
   streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true
6. Add environment variables from .env.example.
7. Deploy.

#### Streamlit Cloud
1. Push this repository to GitHub.
2. Connect the repo to Streamlit Cloud.
3. Use the main file app.py.
4. Add environment variables.
5. Publish the app.

## Required environment variables

- APP_NAME=UmBruM
- APP_URL=https://your-public-domain.com
- STRIPE_SECRET_KEY=live_key_here
- STRIPE_PRICE_50=price_id_here
- STRIPE_PRICE_100=price_id_here
- STRIPE_PRICE_200=price_id_here
- STRIPE_PRICE_400=price_id_here
- OWNER_NAME=BISMARK OSEI OWUSU
- OWNER_EMAIL=monarchmanaois777666@gmail.com
- OWNER_CONTACT=+233 559512438
- OWNER_MTN_WALLET=+233 559512438

## Business rules to preserve exactly

- Every new member receives 50 free credits.
- The free trial lasts 14 days.
- After expiry, the app locks until credits are purchased.
- Members pay for credit packs.
- The owner stays free and unlimited.
- Same rules apply on web and mobile wrapper apps.

## Real money flow

For actual production, these are required:

- live Stripe account
- real product prices
- owner MTN Mobile Money wallet
- payment ledger and approval workflow
- real database instead of local SQLite for production
- secure secret management

## Mobile app store path

The Play Store and App Store do not host raw Streamlit apps directly. To publish on app stores, wrap the public web app inside a mobile app shell.

Recommended options:
- Capacitor with a WebView shell
- React Native WebView wrapper
- a real native mobile app later when the product grows

## Deployment order

1. Deploy web app publicly.
2. Validate the free-trial and paywall flow.
3. Connect Stripe live keys.
4. Confirm owner wallet and payout process.
5. Wrap for Android/iOS if you want store distribution.

## Final recommendation

The best launch model is a public UmBruM web app first, then a mobile wrapper later. This keeps the business model stable while allowing real public rollout and app-store expansion.
