import { corsHeaders, json } from "../_shared/http.ts";
import { admin, authenticatedUser, env, stripe } from "../_shared/services.ts";

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405);
  try {
    const user = await authenticatedUser(req);
    const { data } = await admin.from("subscriptions")
      .select("stripe_customer_id").eq("user_id", user.id).maybeSingle();
    if (!data?.stripe_customer_id) return json({ error: "No billing account found." }, 404);
    const portal = await stripe.billingPortal.sessions.create({
      customer: data.stripe_customer_id,
      return_url: env("APP_URL"),
    });
    return json({ url: portal.url });
  } catch (error) {
    console.error(error);
    return json({ error: error instanceof Error ? error.message : "Billing portal unavailable" }, 400);
  }
});
