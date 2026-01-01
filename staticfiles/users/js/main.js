/* main.js */

/** * 1. Summernote Initialization
 * Checks if jQuery exists before running to avoid the crash seen in your console.
 */
function initSummernote() {
  if (window.jQuery && typeof $.fn.summernote !== "undefined") {
    $("#summernote").summernote({
      height: 300,
      focus: true,
    });
  }
}

/**
 * 2. Auto-Slug Generation
 * Automatically fills the slug as you type the title.
 */
function initSlugGenerator() {
  const titleField = document.querySelector('input[name="title"]');
  const slugField = document.querySelector('input[name="slug"]');

  if (titleField && slugField) {
    titleField.addEventListener("input", function () {
      const slugValue = titleField.value
        .toLowerCase()
        .replace(/[^a-z0-9 -]/g, "") // remove invalid chars
        .replace(/\s+/g, "-") // collapse whitespace and replace by -
        .replace(/-+/g, "-"); // collapse dashes
      slugField.value = slugValue;
    });
  }
}

document.addEventListener("DOMContentLoaded", function () {
  // Run Initializers
  initSummernote();
  initSlugGenerator();

  /* SIDEBAR & OVERLAY LOGIC */
  const sidebar = document.getElementById("sidebar");
  const mobileOverlay = document.getElementById("mobileOverlay");
  const desktopToggle = document.getElementById("desktopSidebarToggle");
  const mobileToggle = document.getElementById("mobileSidebarToggle");

  function toggleSidebar() {
    if (window.innerWidth <= 768) {
      sidebar.classList.toggle("mobile-active");
      if (mobileOverlay) mobileOverlay.classList.toggle("active");
    } else {
      sidebar.classList.toggle("d-none");
    }
  }

  if (desktopToggle) desktopToggle.addEventListener("click", toggleSidebar);
  if (mobileToggle) mobileToggle.addEventListener("click", toggleSidebar);

  /* DARK MODE LOGIC */
  const body = document.body;
  const navbar = document.querySelector(".navbar");
  const darkModeToggle = document.getElementById("darkModeToggle");
  const moon = document.getElementById("moonIcon");
  const sun = document.getElementById("sunIcon");

  if (localStorage.getItem("theme") === "dark") {
    navbar?.classList.add("dark-mode");
    body.classList.add("dark-background");
    moon?.classList.add("d-none");
    sun?.classList.remove("d-none");
  }

  darkModeToggle?.addEventListener("click", function () {
    navbar.classList.toggle("dark-mode");
    body.classList.toggle("dark-background");

    const isDark = navbar.classList.contains("dark-mode");
    localStorage.setItem("theme", isDark ? "dark" : "light");

    if (isDark) {
      moon?.classList.add("d-none");
      sun?.classList.remove("d-none");
    } else {
      sun?.classList.add("d-none");
      moon?.classList.remove("d-none");
    }
  });

  /* ALERT DISMISSAL */
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach((alert) => {
    setTimeout(() => {
      if (alert) {
        // Use Bootstrap method if available, else remove manually
        const bsAlert = window.bootstrap
          ? bootstrap.Alert.getInstance(alert)
          : null;
        if (bsAlert) {
          bsAlert.close();
        } else {
          alert.remove();
        }
      }
    }, 10000);
  });
});
