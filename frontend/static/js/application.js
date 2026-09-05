const applicationForm = document.querySelector("#application-form");

applicationForm?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const button = applicationForm.querySelector("button");
  const status = document.querySelector("#application-status");
  const originalLabel = button.textContent;

  button.disabled = true;
  button.textContent = "Отправляем…";
  status.textContent = "";

  try {
    const response = await fetch(applicationForm.action, {
      method: "POST",
      body: new FormData(applicationForm),
    });
    const result = await response.json();
    if (!response.ok || !result.success) throw new Error("Web3Forms rejected submission");

    document.querySelector("#application-result").innerHTML =
      '<p class="lead-success">Спасибо! Заявка отправлена, скоро свяжемся с вами.</p>';
  } catch (error) {
    status.textContent = "Не удалось отправить заявку. Пожалуйста, попробуйте немного позже.";
    button.disabled = false;
    button.textContent = originalLabel;
  }
});
