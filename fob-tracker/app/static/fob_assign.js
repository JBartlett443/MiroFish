(function () {
  const fob = document.getElementById("fob_uid");
  const captured = document.getElementById("captured");
  const search = document.getElementById("user-search");
  const hidden = document.getElementById("user_id");
  const list = document.getElementById("user-list");

  function markCaptured() {
    if (fob.value.trim()) {
      captured.textContent = "Captured ✓";
    } else {
      captured.textContent = "";
    }
  }
  fob.addEventListener("input", markCaptured);
  markCaptured();

  // Pressing Enter in the fob field moves focus to the user search instead of submitting.
  fob.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      markCaptured();
      search.focus();
    }
  });

  // Resolve the typed value to the matching option's data-id.
  function syncHidden() {
    const val = search.value;
    const opt = Array.from(list.options).find((o) => o.value === val);
    hidden.value = opt ? opt.getAttribute("data-id") : "";
  }
  search.addEventListener("input", syncHidden);
  search.addEventListener("change", syncHidden);

  document.getElementById("assign-form").addEventListener("submit", (e) => {
    syncHidden();
    if (!hidden.value) {
      e.preventDefault();
      alert("Pick a user from the list.");
      search.focus();
    }
  });
})();
