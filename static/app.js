// Small enhancements for server-rendered pages. Pages work without this file.

// "Add another" buttons for Django formsets. The button's data-add-form names the
// formset prefix. The page holds the empty row in <template id="PREFIX-empty">
// and the rows in an element with id="PREFIX-rows".
document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-add-form]");
  if (!button) return;
  const prefix = button.dataset.addForm;
  const total = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
  const template = document.getElementById(`${prefix}-empty`);
  const row = template.innerHTML.replaceAll("__prefix__", total.value);
  document.getElementById(`${prefix}-rows`).insertAdjacentHTML("beforeend", row);
  total.value = Number(total.value) + 1;
});

// Forms with data-confirm ask before submitting, for actions that delete or replace data.
document.addEventListener("submit", (event) => {
  const message = event.target.dataset.confirm;
  if (message && !window.confirm(message)) event.preventDefault();
});

// Search boxes with data-filter="ID" hide the [data-filter-item] elements inside
// #ID whose text doesn't contain the search. Checked items always stay visible.
document.addEventListener("input", (event) => {
  const target = event.target.dataset.filter;
  if (!target) return;
  const query = event.target.value.trim().toLowerCase();
  for (const item of document.getElementById(target).querySelectorAll("[data-filter-item]")) {
    const checked = item.querySelector("input:checked");
    item.hidden = !checked && !item.textContent.toLowerCase().includes(query);
  }
});
