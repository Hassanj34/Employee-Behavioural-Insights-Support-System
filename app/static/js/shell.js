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
    if (event.key === "Escape") {
      closeMenu();
      closeNotifications();
    }
  });

  const notifyButton = document.getElementById("notify-button");
  const notifyPanel = document.getElementById("notify-panel");

  function closeNotifications() {
    if (!notifyPanel || !notifyButton) return;
    notifyPanel.hidden = true;
    notifyButton.setAttribute("aria-expanded", "false");
  }

  function markNotificationsRead() {
    const badge = notifyButton.querySelector(".notify-badge");
    if (!badge) return;
    const token = document.querySelector('meta[name="csrf-token"]');
    const hidden = notifyButton.querySelector(".visually-hidden");
    badge.remove();
    if (hidden) hidden.textContent = "Notifications";
    fetch("/notifications/read", {
      method: "POST",
      headers: {
        "X-CSRFToken": token ? token.content : "",
        "Accept": "application/json",
      },
    }).then(function (response) {
      if (!response.ok) {
        notifyButton.insertBefore(badge, hidden);
        return;
      }
      notifyPanel.querySelectorAll(".notify-item.is-unread").forEach(function (item) {
        item.classList.remove("is-unread");
      });
    }).catch(function () {
      notifyButton.insertBefore(badge, hidden);
    });
  }

  function clearNotifications() {
    const token = document.querySelector('meta[name="csrf-token"]');
    const clearButton = document.getElementById("notify-clear");
    if (clearButton) clearButton.disabled = true;
    fetch("/notifications/clear", {
      method: "POST",
      headers: {
        "X-CSRFToken": token ? token.content : "",
        "Accept": "application/json",
      },
    }).then(function (response) {
      if (!response.ok) {
        if (clearButton) clearButton.disabled = false;
        return;
      }
      const badge = notifyButton.querySelector(".notify-badge");
      if (badge) badge.remove();
      const list = notifyPanel.querySelector(".notify-list");
      if (list) list.remove();
      if (clearButton) clearButton.remove();
      if (!notifyPanel.querySelector(".notify-empty")) {
        const empty = document.createElement("p");
        empty.className = "notify-empty";
        empty.textContent = "No notifications.";
        notifyPanel.appendChild(empty);
      }
    }).catch(function () {
      if (clearButton) clearButton.disabled = false;
    });
  }

  if (notifyButton && notifyPanel) {
    notifyButton.addEventListener("click", function (event) {
      event.stopPropagation();
      const willOpen = notifyPanel.hidden;
      if (willOpen) {
        notifyPanel.hidden = false;
        notifyButton.setAttribute("aria-expanded", "true");
        markNotificationsRead();
      } else {
        closeNotifications();
      }
    });
    notifyPanel.addEventListener("click", function (event) {
      const clearButton = event.target.closest("#notify-clear");
      if (!clearButton) return;
      event.preventDefault();
      event.stopPropagation();
      clearNotifications();
    });
    notifyPanel.addEventListener("click", function (event) {
      event.stopPropagation();
    });
    document.addEventListener("click", closeNotifications);
  }

  document.querySelectorAll(".filter-bar select, .filter-bar input[type=date]").forEach(function (field) {
    field.addEventListener("change", function () {
      if (field.form) field.form.requestSubmit();
    });
  });
})();
