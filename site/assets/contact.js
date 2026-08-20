(function () {
  var form = document.getElementById("custom-data-form");
  if (!form) return;
  var status = document.getElementById("form-status");
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;
    status.textContent = "Sending…";
    var payload = {
      name: form.name.value,
      email: form.email.value,
      company: form.company.value,
      volume: form.volume.value,
      need: form.need.value,
      company_website: form.company_website.value,
    };
    var endpoint = /dosevault\.health$/.test(location.hostname)
      ? "/api/contact"
      : "https://testdata-dosevault.netlify.app/api/contact";
    fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (r) {
        return r.json().then(function (j) {
          return { ok: r.ok, j: j };
        });
      })
      .then(function (res) {
        if (res.ok && res.j.ok) {
          status.textContent = "Sent. We will reply from a CODEAMANI LABS address.";
          form.reset();
        } else {
          status.textContent = (res.j && res.j.error) || "Could not send. Email hq@codeamanilabs.com.";
        }
      })
      .catch(function () {
        status.textContent = "Network error. Email hq@codeamanilabs.com.";
      })
      .finally(function () {
        btn.disabled = false;
      });
  });
})();
