(function () {
  const fob = document.getElementById("fob");
  const idle = document.getElementById("idle");
  const result = document.getElementById("result");
  const direction = document.getElementById("direction");
  const nameEl = document.getElementById("name");
  const timeEl = document.getElementById("time");
  const clock = document.getElementById("clock");

  // Tweak if your reader prefixes/suffixes anything (e.g. leading zeros).
  function cleanUid(raw) {
    return raw.replace(/\s+/g, "").trim();
  }

  function tickClock() {
    const d = new Date();
    const hh = String(d.getHours()).padStart(2, "0");
    const mm = String(d.getMinutes()).padStart(2, "0");
    clock.textContent = `${hh}:${mm}`;
  }
  tickClock();
  setInterval(tickClock, 10_000);

  function keepFocus() {
    if (document.activeElement !== fob) fob.focus();
  }
  setInterval(keepFocus, 500);
  document.addEventListener("click", keepFocus);
  window.addEventListener("focus", keepFocus);
  keepFocus();

  function showResult(payload) {
    idle.classList.add("hidden");
    result.classList.remove("hidden");
    document.body.classList.remove("flash-in", "flash-out", "flash-unknown");

    if (payload.status === "ok") {
      direction.textContent = payload.direction === "IN" ? "Clocked IN" : "Clocked OUT";
      nameEl.textContent = payload.name;
      timeEl.textContent = payload.time;
      document.body.classList.add(payload.direction === "IN" ? "flash-in" : "flash-out");
    } else if (payload.status === "unknown") {
      direction.textContent = "Unknown fob";
      nameEl.textContent = payload.fob_uid;
      timeEl.textContent = "See the manager";
      document.body.classList.add("flash-unknown");
    } else if (payload.status === "inactive") {
      direction.textContent = "Inactive user";
      nameEl.textContent = payload.fob_uid;
      timeEl.textContent = "See the manager";
      document.body.classList.add("flash-unknown");
    } else {
      direction.textContent = "Error";
      nameEl.textContent = payload.message || "Please try again";
      timeEl.textContent = "";
      document.body.classList.add("flash-unknown");
    }

    setTimeout(() => {
      idle.classList.remove("hidden");
      result.classList.add("hidden");
      document.body.classList.remove("flash-in", "flash-out", "flash-unknown");
      fob.value = "";
      keepFocus();
    }, 3000);
  }

  fob.addEventListener("keydown", async (e) => {
    if (e.key !== "Enter") return;
    e.preventDefault();
    const uid = cleanUid(fob.value);
    fob.value = "";
    if (!uid) return;
    try {
      const resp = await fetch("/scan/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fob_uid: uid }),
      });
      const payload = await resp.json();
      showResult(payload);
    } catch (err) {
      showResult({ status: "error", message: "Network error" });
    }
  });
})();
