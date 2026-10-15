(function () {
  const clock = document.getElementById("live-clock");
  function tickClock() {
    const d = new Date();
    const hh = String(d.getHours()).padStart(2, "0");
    const mm = String(d.getMinutes()).padStart(2, "0");
    if (clock) clock.textContent = `${hh}:${mm}`;
  }
  tickClock();
  setInterval(tickClock, 10_000);

  async function refresh() {
    try {
      const r = await fetch("/admin/stats.json", { credentials: "same-origin" });
      if (!r.ok) return;
      const s = await r.json();

      document.getElementById("scans-today").textContent = s.scans_today;
      document.getElementById("people-today").textContent = s.people_today;
      document.getElementById("last-hour").textContent = s.scans_last_hour;
      document.getElementById("week-total").textContent = s.week_total_hours;

      const ci = document.getElementById("currently-in");
      if (ci) {
        if (s.currently_in.length === 0) {
          ci.outerHTML = '<p class="empty">No one is clocked in right now.</p>';
        } else {
          ci.innerHTML = s.currently_in.map(p =>
            `<li><span class="pname">${escapeHtml(p.name)}</span><span class="pmeta">since ${p.since} · ${p.elapsed}</span></li>`
          ).join("");
        }
      }

      const recent = document.querySelector("#recent tbody");
      if (recent) {
        if (!s.recent.length) {
          recent.innerHTML = '<tr><td colspan="4" class="empty">No scans yet.</td></tr>';
        } else {
          recent.innerHTML = s.recent.map(r =>
            `<tr><td class="rname">${escapeHtml(r.name)}</td>` +
            `<td><span class="pill pill-${r.direction.toLowerCase()}">${r.direction}</span></td>` +
            `<td class="rtime">${r.time}</td>` +
            `<td>${r.manual ? '<span class="pill pill-manual">manual</span>' : ''}</td></tr>`
          ).join("");
        }
      }
    } catch (e) { /* ignore */ }
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  }

  setInterval(refresh, 30_000);
})();
