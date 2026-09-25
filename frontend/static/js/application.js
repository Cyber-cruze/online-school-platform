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
    const name = String(formData.get("name") || "").trim();
    const phone = String(formData.get("phone") || "").trim();
    const email = String(formData.get("email") || "").trim();

    formData.set("subject", "Заявка на консультацию — школа Стимул");
    formData.set("from_name", "Онлайн-школа Стимул");
    formData.set(
      "message",
      [
        "Получена заявка с сайта онлайн-школы «Стимул».",
        "",
        `Имя: ${name}`,
        `Телефон: ${phone}`,
        `Электронная почта: ${email}`,
        "",
        "Посетитель ожидает обратной связи по указанным контактам.",
      ].join("\n"),
    );
    formData.delete("name");
    formData.delete("phone");

    const response = await fetch(applicationForm.action, {
      method: "POST",
      body: formData,
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
