import { json } from "../_shared/http.ts";
import { admin, env, stripe } from "../_shared/services.ts";
import Stripe from "npm:stripe@18.5.0";

async function saveSubscription(subscription: Stripe.Subscription) {
  const customerId = typeof subscription.customer === "string" ? subscription.customer : subscription.customer.id;
  let userId = subscription.metadata.supabase_user_id;
  if (!userId) {
    const { data } = await admin.from("subscriptions").select("user_id")
      .eq("stripe_customer_id", customerId).maybeSingle();
    userId = data?.user_id;
  }
  if (!userId) throw new Error(`No Supabase user mapping for Stripe customer ${customerId}`);
  const item = subscription.items.data[0];
  const periodEnd = item?.current_period_end
    ? new Date(item.current_period_end * 1000).toISOString() : null;
  const { error } = await admin.from("subscriptions").upsert({
    user_id: userId,
    stripe_customer_id: customerId,
    stripe_subscription_id: subscription.id,
    price_id: item?.price?.id || null,
    status: subscription.status,
    current_period_end: periodEnd,
    cancel_at_period_end: subscription.cancel_at_period_end,
    updated_at: new Date().toISOString(),
  }, { onConflict: "user_id" });
  if (error) throw error;
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405);
  const signature = req.headers.get("stripe-signature");
  if (!signature) return json({ error: "Missing Stripe signature" }, 400);
  try {
    const event = await stripe.webhooks.constructEventAsync(
      await req.text(), signature, env("STRIPE_WEBHOOK_SECRET"));
    if (["customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"].includes(event.type)) {
      await saveSubscription(event.data.object as Stripe.Subscription);
    }
    return json({ received: true });
  } catch (error) {
    console.error(error);
    return json({ error: "Invalid webhook" }, 400);
  }
});
