import { corsHeaders, json } from "../_shared/http.ts";
import { admin, authenticatedUser, env, stripe } from "../_shared/services.ts";

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405);
  try {
    const user = await authenticatedUser(req);
    const { data: record } = await admin.from("subscriptions")
      .select("stripe_customer_id,status").eq("user_id", user.id).maybeSingle();
    if (["active", "trialing"].includes(record?.status || "")) {
      return json({ error: "This account already has an active subscription." }, 409);
    }

    let customerId = record?.stripe_customer_id as string | undefined;
    if (!customerId) {
      const customer = await stripe.customers.create({
        email: user.email,
        metadata: { supabase_user_id: user.id },
      });
      customerId = customer.id;
      await admin.from("subscriptions").upsert({
        user_id: user.id, stripe_customer_id: customerId, status: "none", updated_at: new Date().toISOString(),
      }, { onConflict: "user_id" });
    }

    const appUrl = env("APP_URL").replace(/\/$/, "");
    const checkout = await stripe.checkout.sessions.create({
      mode: "subscription",
      customer: customerId,
      line_items: [{ price: env("STRIPE_PRICE_ID"), quantity: 1 }],
      client_reference_id: user.id,
      metadata: { supabase_user_id: user.id },
      subscription_data: { metadata: { supabase_user_id: user.id } },
      allow_promotion_codes: false,
      success_url: `${appUrl}/?checkout=success&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${appUrl}/?checkout=cancelled`,
    });
    return json({ url: checkout.url });
  } catch (error) {
    console.error(error);
    return json({ error: error instanceof Error ? error.message : "Checkout unavailable" }, 400);
  }
});
