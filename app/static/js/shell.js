(function () {
  const button = document.getElementById("menu-toggle");
  const sidebar = document.getElementById("sidebar");
  const scrim = document.getElementById("scrim");
  if (!button || !sidebar) return;

  function closeMenu() {
    sidebar.classList.remove("open");
    if (scrim) scrim.hidden = true;
    button.setAttribute("aria-expanded", "false");
  }

  function openMenu() {
    sidebar.classList.add("open");
    if (scrim) scrim.hidden = false;
    button.setAttribute("aria-expanded", "true");
  }

  button.addEventListener("click", function () {
    if (sidebar.classList.contains("open")) closeMenu();
    else openMenu();
  });
  if (scrim) scrim.addEventListener("click", closeMenu);
  sidebar.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", closeMenu);
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeMenu();
  });

  document.querySelectorAll(".filter-bar select, .filter-bar input[type=date]").forEach(function (field) {
    field.addEventListener("change", function () {
      if (field.form) field.form.requestSubmit();
    });
  });
})();
