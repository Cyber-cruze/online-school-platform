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
    const formData = new FormData(applicationForm);
    const payload = {
      name: String(formData.get("name") || "").trim(),
      phone: String(formData.get("phone") || "").trim(),
      email: String(formData.get("email") || "").trim(),
      botcheck: formData.get("botcheck") ? "filled" : "",
    };

    if (!payload.name || !payload.phone || !payload.email) {
      throw new Error("validation");
    }

    const response = await fetch(applicationForm.action, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (response.status === 422) throw new Error("validation");
    if (!response.ok) throw new Error("delivery");
    const result = await response.json();
    if (!result.success) throw new Error("delivery");

    document.querySelector("#application-result").innerHTML =
      '<p class="lead-success">Спасибо! Заявка отправлена, скоро свяжемся с вами.</p>';
  } catch (error) {
    status.textContent = error.message === "validation"
      ? "Проверьте имя, телефон и электронную почту."
      : "Не удалось отправить заявку. Пожалуйста, попробуйте немного позже.";
    button.disabled = false;
    button.textContent = originalLabel;
  }
});
