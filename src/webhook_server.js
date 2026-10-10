const http = require('http');
const url = require('url');

const PORT = 8080;

const OFFICIAL_PRICING = {
  "Mini Leader": {
    "annual_cost_inr": 28000,
    "monthly_equivalent_inr": 2333,
    "verified_leads_per_month": 45,
    "features": [
      "Top district search listing",
      "Direct phone calls from OTP-verified buyers",
      "IndiaMART verified trust seal logo",
      "Free catalog setup & photos upload"
    ],
    "suitable_for": "Micro & Small MSMEs (Turnover under 1.5 Cr)"
  },
  "TrustSEAL Verified": {
    "annual_cost_inr": 48000,
    "monthly_equivalent_inr": 4000,
    "verified_leads_per_month": 90,
    "features": [
      "TrustSEAL background check badge",
      "State-level top priority ranking",
      "Instant WhatsApp & SMS lead alert",
      "Escrow protection with Pay with IndiaMART"
    ],
    "suitable_for": "Medium MSMEs (Turnover 1.5 - 5 Cr)"
  },
  "Maximiser Star": {
    "annual_cost_inr": 85000,
    "monthly_equivalent_inr": 7083,
    "verified_leads_per_month": 180,
    "features": [
      "Pan-India top 3 guaranteed placement",
      "Dedicated Relationship Manager (RM)",
      "Unlimited verified buy-leads consumption",
      "Export lead access & multi-city targeting"
    ],
    "suitable_for": "Large & Enterprise Manufacturers (Turnover 5+ Cr)"
  }
};

const VERIFIED_BUYER_DEMAND = {
  "Cotton Yarn": { active_buyers: 18, avg_order_value: "₹3.5 Lakh", top_cities: ["Surat", "Coimbatore", "Ludhiana", "Bhilwara"] },
  "Industrial Valves & Fittings": { active_buyers: 14, avg_order_value: "₹1.8 Lakh", top_cities: ["Ahmedabad", "Pune", "Delhi NCR", "Chennai"] },
  "Textiles & Garments": { active_buyers: 26, avg_order_value: "₹2.2 Lakh", top_cities: ["Surat", "Jaipur", "Tiruppur", "Kolkata"] },
  "Ceramic Floor Tiles": { active_buyers: 12, avg_order_value: "₹4.0 Lakh", top_cities: ["Morbi", "Delhi", "Bengaluru", "Hyderabad"] },
  "Color Coating Services": { active_buyers: 9, avg_order_value: "₹5.5 Lakh", top_cities: ["Faridabad", "Pune", "Manesar", "Bhiwadi"] },
  "UPVC Sliding Windows": { active_buyers: 28, avg_order_value: "₹2.8 Lakh", top_cities: ["Patna", "Ranchi", "Varanasi", "Lucknow"] },
  "Brass God Statues": { active_buyers: 15, avg_order_value: "₹1.2 Lakh", top_cities: ["Jaipur", "Moradabad", "Delhi", "Ahmedabad"] },
  "Dangling Earring": { active_buyers: 22, avg_order_value: "₹85,000", top_cities: ["Mumbai", "Jaipur", "Surat", "Kolkata"] },
  "General Goods": { active_buyers: 15, avg_order_value: "₹1.5 Lakh", top_cities: ["Delhi", "Mumbai", "Jaipur", "Kanpur"] }
};

function getVerifiedBuyerLeads(category, stateOrCity) {
  const cleanCat = (category || "").trim().toLowerCase();
  let matchedKey = "General Goods";
  for (const k of Object.keys(VERIFIED_BUYER_DEMAND)) {
    if (k.toLowerCase().includes(cleanCat) || cleanCat.includes(k.toLowerCase())) {
      matchedKey = k;
      break;
    }
  }
  const demand = VERIFIED_BUYER_DEMAND[matchedKey] || VERIFIED_BUYER_DEMAND["General Goods"];
  return {
    category: matchedKey,
    region_filter: stateOrCity || "All India",
    active_verified_buyers: demand.active_buyers,
    avg_order_value: demand.avg_order_value,
    high_demand_clusters: demand.top_cities,
    verification_standard: "100% Mobile OTP & GST verified",
    spoken_script_hindi: `Aapke ${matchedKey} ke liye pichle hafte ${demand.active_buyers} verified buyers ne quotation manga hai.`
  };
}

function getOfficialPricing(turnover) {
  const isEnterprise = ["5 - 25 Cr", "25 - 100 Cr", "100+ Cr", "Enterprise", "Large"].some(t => (turnover || "").includes(t));
  const recommended = isEnterprise ? "Maximiser Star" : "Mini Leader";
  return {
    package_name: recommended,
    monthly_starting_cost: "Approx ₹2,000 se ₹2,500 mahina (saalaana ₹28,000 + GST)",
    pricing_explanation: "Monthly 2,000 se 2,500 ke hisaab se start hota hai Mini Leader plan, jisme verified buyers aapko direct contact karte hain.",
    tiers: OFFICIAL_PRICING
  };
}

function bookSlot(sellerId, date, timeSlot, channel = "phone") {
  const safeDate = date || "Tomorrow";
  const safeTime = timeSlot || "11:00 AM";
  const bookingId = `IM-RM-${Math.floor(100000 + Math.random() * 900000)}`;
  return {
    status: "confirmed",
    booking_id: bookingId,
    seller_id: sellerId || "UNKNOWN",
    scheduled_date: safeDate,
    scheduled_time: safeTime,
    meeting_type: (channel || "").toLowerCase().includes("phone") ? "Phone Consultation" : "In-Person Shop Visit",
    confirmation_message: `Meeting confirmed with Relationship Manager on ${safeDate} at ${safeTime}.`
  };
}

const server = http.createServer((req, res) => {
  const parsed = url.parse(req.url, true);
  const path = parsed.pathname;

  // CORS headers
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

  if (req.method === "OPTIONS") {
    res.writeHead(200);
    return res.end();
  }

  if (req.method === "GET") {
    if (path === "/health") {
      res.writeHead(200, { "Content-Type": "application/json" });
      return res.end(JSON.stringify({ status: "healthy", service: "sarvam-indiamart-bridge", port: PORT }));
    }
    res.writeHead(404, { "Content-Type": "application/json" });
    return res.end(JSON.stringify({ error: "Not found" }));
  }

  if (req.method === "POST") {
    let body = "";
    req.on("data", chunk => { body += chunk; });
    req.on("end", () => {
      let payload = {};
      try {
        if (body) payload = JSON.parse(body);
      } catch (e) {
        res.writeHead(400, { "Content-Type": "application/json" });
        return res.end(JSON.stringify({ error: "Invalid JSON" }));
      }

      console.log(`[POST ${path}] Received payload:`, payload);

      let result = {};
      if (path === "/api/tools/buyer_leads") {
        const cat = payload.category || payload.top_category_1 || "General Goods";
        const loc = payload.state_or_city || payload.seller_state || "";
        result = getVerifiedBuyerLeads(cat, loc);
      } else if (path === "/api/tools/pricing") {
        result = getOfficialPricing(payload.turnover || "");
      } else if (path === "/api/tools/book_slot") {
        result = bookSlot(payload.seller_id, payload.date, payload.time_slot, payload.channel);
      } else if (path === "/webhook/on-start") {
        result = { status: "success", opening_line: "Namaste ji, main IndiaMART se bol raha hoon." };
      } else if (path === "/webhook/on-end") {
        result = { status: "recorded", disposition: payload.call_disposition || "meeting_fixed" };
      } else {
        res.writeHead(404, { "Content-Type": "application/json" });
        return res.end(JSON.stringify({ error: `Unknown endpoint ${path}` }));
      }

      console.log(`[POST ${path}] Responding:`, result);
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify(result));
    });
  }
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`IndiaMART VANI Webhook Server running on http://0.0.0.0:${PORT}`);
});
