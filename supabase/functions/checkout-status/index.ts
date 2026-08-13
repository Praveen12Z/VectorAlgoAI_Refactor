import { corsHeaders, json } from "../_shared/http.ts";
import { stripe } from "../_shared/services.ts";

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405);

  try {
    const { session_id: sessionId } = await req.json();
    if (typeof sessionId !== "string" || !sessionId.startsWith("cs_")) {
      return json({ error: "Invalid checkout session" }, 400);
    }

    const checkout = await stripe.checkout.sessions.retrieve(sessionId);
    return json({
      status: checkout.status,
      payment_status: checkout.payment_status,
    });
  } catch (error) {
    console.error(error);
    return json({ error: "Unable to verify this payment" }, 400);
  }
});
