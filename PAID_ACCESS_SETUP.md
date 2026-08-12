# VectorAlgoAI paid-access deployment

The Streamlit app uses the public Supabase URL and publishable key. Stripe and
the Supabase service-role key are used only by Supabase Edge Functions.

## Required Supabase function secrets

- `STRIPE_SECRET_KEY`: Stripe test-mode secret key during testing
- `STRIPE_PRICE_ID`: the existing €18.99 monthly test-mode Price ID
- `STRIPE_WEBHOOK_SECRET`: signing secret for the deployed webhook endpoint
- `APP_URL`: `https://vectoralgoai.streamlit.app`

`SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are available to deployed
Supabase Edge Functions by default.

## Deploy in test mode

1. Apply `supabase/migrations/20260812_paid_access.sql` in the SQL Editor. It is
   safe to apply after the table created during setup.
2. Add the four function secrets above in Supabase.
3. Deploy `create-checkout`, `customer-portal`, and `stripe-webhook`.
4. In Stripe test mode, register this endpoint:
   `https://<project-ref>.supabase.co/functions/v1/stripe-webhook`
5. Subscribe it to `customer.subscription.created`,
   `customer.subscription.updated`, and `customer.subscription.deleted`.
6. Copy Stripe's endpoint signing secret into `STRIPE_WEBHOOK_SECRET` and
   redeploy/restart the webhook function if required.
7. Keep Streamlit sharing private and run signup, confirmation, test checkout,
   renewal/status, cancellation, and failed-payment tests.
8. Switch to live Stripe keys and the live €18.99 recurring Price ID only after
   every test passes, then repeat a low-risk live end-to-end verification.

## Security invariants

- Checkout success redirects never grant access.
- Only `active` and `trialing` subscription states unlock Strategy Lab.
- Missing configuration, request failures, and missing subscription rows fail closed.
- Users may select only their own subscription row under Row Level Security.
- Stripe secrets and the Supabase service-role key never belong in Streamlit Secrets.
