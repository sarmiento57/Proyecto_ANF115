document.addEventListener("DOMContentLoaded", function () {
  const phoneInput = document.getElementById("phone");

  if (phoneInput) {
    phoneInput.addEventListener("input", function (e) {
      let value = e.target.value.replace(/\D/g, "");
      if (value.length > 8) value = value.slice(0, 8);

      if (value.length > 4) {
        value = value.slice(0, 4) + "-" + value.slice(4);
      }
      e.target.value = value;
    });
  }
});
