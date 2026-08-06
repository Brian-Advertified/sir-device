(() => {
  const cartCountKey = "sir-device-cart-count";

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";

  const renderCartCount = (count) => {
    const safeCount = Number.isFinite(count) ? count : 0;
    localStorage.setItem(cartCountKey, String(safeCount));
    document.querySelectorAll("[data-cart-count]").forEach((element) => {
      element.textContent = String(safeCount);
    });
  };

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-add-cart]");
    if (!button) return;
    button.disabled = true;
    const originalText = button.textContent;
    button.textContent = "Adding…";
    try {
      const response = await fetch("/api/v1/cart/items", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken,
        },
        body: JSON.stringify({ deal_id: button.dataset.addCart, quantity: 1 }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "Could not add this product");
      renderCartCount(payload.item_count);
      button.textContent = "Added to cart";
      window.setTimeout(() => { button.textContent = originalText; }, 1300);
    } catch (error) {
      window.alert(error.message);
      button.textContent = originalText;
    } finally {
      button.disabled = false;
    }
  });

  const savedCount = Number.parseInt(localStorage.getItem(cartCountKey) || "0", 10);
  renderCartCount(Number.isFinite(savedCount) ? savedCount : 0);
})();
