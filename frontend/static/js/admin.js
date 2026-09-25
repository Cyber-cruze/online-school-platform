document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-edit-toggle]");
  if (!button) return;

  const editor = document.getElementById(button.dataset.editToggle);
  if (!editor) return;

  const isOpen = button.getAttribute("aria-expanded") === "true";
  button.setAttribute("aria-expanded", String(!isOpen));
  button.textContent = isOpen ? "Редактировать" : "Закрыть";
  editor.hidden = isOpen;
});
