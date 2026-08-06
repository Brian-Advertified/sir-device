(() => {
  const storageKey = "sir-device-compare";
  const maxCompare = 3;

  const readIds = () => {
    try {
      const value = JSON.parse(localStorage.getItem(storageKey) || "[]");
      return Array.isArray(value) ? value.filter((item) => typeof item === "string").slice(0, maxCompare) : [];
    } catch {
      return [];
    }
  };

  const writeIds = (ids) => {
    localStorage.setItem(storageKey, JSON.stringify(ids.slice(0, maxCompare)));
    renderCompareState();
  };

  const renderCompareState = () => {
    const ids = readIds();
    document.querySelectorAll("[data-compare-count]").forEach((element) => {
      element.textContent = String(ids.length);
    });
    document.querySelectorAll("[data-compare-link]").forEach((element) => {
      element.href = `/compare?ids=${encodeURIComponent(ids.join(","))}`;
    });
    document.querySelectorAll("[data-compare-add]").forEach((button) => {
      const selected = ids.includes(button.dataset.compareAdd);
      button.textContent = selected ? "Added" : "Compare";
      button.setAttribute("aria-pressed", selected ? "true" : "false");
    });
  };

  const variantSelections = {};
  document.querySelectorAll("[data-variant-group].active").forEach((button) => {
    variantSelections[button.dataset.variantGroup] = button.dataset.variantValue;
  });

  const renderVariantState = () => {
    document.querySelectorAll("[data-variant-group]").forEach((button) => {
      const selected = variantSelections[button.dataset.variantGroup] === button.dataset.variantValue;
      button.classList.toggle("active", selected);
      button.setAttribute("aria-pressed", selected ? "true" : "false");
    });
    document.querySelectorAll("[data-selected-variant]").forEach((element) => {
      const value = variantSelections[element.dataset.selectedVariant];
      if (value) element.textContent = value;
    });
    document.querySelectorAll("[data-variant-action]").forEach((link) => {
      const url = new URL(link.dataset.baseHref, window.location.origin);
      Object.entries(variantSelections).forEach(([key, value]) => url.searchParams.set(key, value));
      link.href = `${url.pathname}${url.search}${url.hash}`;
    });
  };

  document.addEventListener("click", (event) => {
    const galleryThumb = event.target.closest("[data-gallery-thumb]");
    if (galleryThumb) {
      const mainImage = document.querySelector("[data-gallery-main]");
      if (mainImage) {
        mainImage.src = galleryThumb.dataset.imageUrl;
        mainImage.alt = galleryThumb.dataset.imageAlt || "Product image";
      }
      document.querySelectorAll("[data-gallery-thumb]").forEach((thumb) => thumb.classList.toggle("active", thumb === galleryThumb));
    }

    const variantButton = event.target.closest("[data-variant-group]");
    if (variantButton) {
      variantSelections[variantButton.dataset.variantGroup] = variantButton.dataset.variantValue;
      renderVariantState();
    }

    const addButton = event.target.closest("[data-compare-add]");
    if (addButton) {
      const ids = readIds();
      const id = addButton.dataset.compareAdd;
      if (ids.includes(id)) {
        writeIds(ids.filter((item) => item !== id));
      } else if (ids.length < maxCompare) {
        writeIds([...ids, id]);
      } else {
        window.alert("You can compare up to three offers.");
      }
    }

    const removeButton = event.target.closest("[data-compare-remove]");
    if (removeButton) {
      writeIds(readIds().filter((item) => item !== removeButton.dataset.compareRemove));
      window.location.href = `/compare?ids=${encodeURIComponent(readIds().join(","))}`;
    }

    if (event.target.closest("[data-compare-clear]")) {
      writeIds([]);
      window.location.href = "/compare";
    }
  });

  const navToggle = document.querySelector("[data-nav-toggle]");
  const nav = document.querySelector("[data-primary-nav]");
  navToggle?.addEventListener("click", () => nav?.classList.toggle("open"));

  const customerType = document.querySelector("[data-customer-type]");
  const personalFields = document.querySelector("[data-personal-fields]");
  const businessFields = document.querySelector("[data-business-fields]");
  const switchFields = () => {
    if (!customerType || !personalFields || !businessFields) return;
    const business = customerType.value === "business";
    personalFields.hidden = business;
    businessFields.hidden = !business;
  };
  customerType?.addEventListener("change", switchFields);
  switchFields();
  renderCompareState();
  renderVariantState();
})();
