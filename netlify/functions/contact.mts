/**
 * Public custom-dataset inquiry. Sends via Resend. Not PHI.
 */
const TO = [
  "hq@codeamanilabs.com",
  "info@codeamani.com",
  "data@codeamanilabs.org",
];

const FROM = "Florida Synthetic Health <data@codeamanilabs.org>";

function escapeHtml(s: string) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export default async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("", { status: 204, headers: cors(req) });
  }
  if (req.method !== "POST") {
    return json({ error: "Method not allowed" }, 405, req);
  }

  const key =
    (typeof Netlify !== "undefined" && Netlify.env && Netlify.env.get("RESEND_API_KEY")) ||
    process.env.RESEND_API_KEY;
  if (!key) {
    return json({ error: "Mail is not configured" }, 503, req);
  }

  let body: Record<string, string> = {};
  try {
    body = await req.json();
  } catch {
    return json({ error: "Invalid JSON" }, 400, req);
  }

  // Honeypot
  if (body.company_website) {
    return json({ ok: true }, 200, req);
  }

  const name = String(body.name || "").trim().slice(0, 120);
  const email = String(body.email || "").trim().slice(0, 200);
  const company = String(body.company || "").trim().slice(0, 160);
  const need = String(body.need || "").trim().slice(0, 4000);
  const volume = String(body.volume || "").trim().slice(0, 80);

  if (!name || !email || !need) {
    return json({ error: "Name, work email, and a short description are required." }, 400, req);
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return json({ error: "Enter a valid work email." }, 400, req);
  }

  const text = [
    "Custom synthetic dataset request (Florida Synthetic Health)",
    "",
    `Name: ${name}`,
    `Email: ${email}`,
    `Company: ${company || "(not given)"}`,
    `Approx volume: ${volume || "(not given)"}`,
    "",
    need,
    "",
    "SYNTHETIC DATA INQUIRY — do not attach real PHI in replies unless a BAA is in place.",
  ].join("\n");

  const html = `<p>Custom synthetic dataset request from the Florida Synthetic Health site.</p>
<table>
<tr><th align="left">Name</th><td>${escapeHtml(name)}</td></tr>
<tr><th align="left">Email</th><td>${escapeHtml(email)}</td></tr>
<tr><th align="left">Company</th><td>${escapeHtml(company || "(not given)")}</td></tr>
<tr><th align="left">Volume</th><td>${escapeHtml(volume || "(not given)")}</td></tr>
</table>
<pre>${escapeHtml(need)}</pre>
<p><em>Synthetic-data inquiry. Do not attach real PHI unless a BAA is in place.</em></p>`;

  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: FROM,
      to: TO,
      reply_to: email,
      subject: `[synthetic data] ${company || name}`,
      text,
      html,
    }),
  });

  if (!res.ok) {
    return json({ error: "Could not send just now. Email hq@codeamanilabs.com." }, 502, req);
  }

  return json({ ok: true }, 200, req);
};

export const config = {
  path: "/api/contact",
};

function cors(req: Request) {
  const origin = req.headers.get("origin") || "";
  const allowed = [
    "https://testdata.dosevault.health",
    "https://synthetic-pii.dosevault.health",
    "https://sythentic-pii.dosevault.health",
    "https://codeamani-labs.github.io",
  ];
  const allow = allowed.includes(origin) ? origin : allowed[0];
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "content-type",
  };
}

function json(obj: unknown, status: number, req: Request) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", ...cors(req) },
  });
}
