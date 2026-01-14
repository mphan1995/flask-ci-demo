import { qsa } from "./dom.js";

export function setupTabs(tabSelector = ".tab-btn", sectionSelector = ".tab") {
  const tabs = qsa(tabSelector);
  const sections = qsa(sectionSelector);
  tabs.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabs.forEach((tab) => tab.classList.remove("active"));
      sections.forEach((section) => section.classList.remove("active"));
      btn.classList.add("active");
      const target = document.getElementById(`tab-${btn.dataset.tab}`);
      if (target) target.classList.add("active");
    });
  });
}
