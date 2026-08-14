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

  const featuredCarousel = document.querySelector("[data-featured-carousel]");
  const featuredPrevious = document.querySelector("[data-featured-prev]");
  const featuredNext = document.querySelector("[data-featured-next]");
  const updateFeaturedControls = () => {
    if (!featuredCarousel) return;
    const maxScroll = featuredCarousel.scrollWidth - featuredCarousel.clientWidth;
    if (featuredPrevious) featuredPrevious.disabled = featuredCarousel.scrollLeft <= 1;
    if (featuredNext) featuredNext.disabled = featuredCarousel.scrollLeft >= maxScroll - 1;
  };
  const scrollFeatured = (direction) => {
    featuredCarousel?.scrollBy({ left: direction * featuredCarousel.clientWidth, behavior: "smooth" });
  };
  featuredPrevious?.addEventListener("click", () => scrollFeatured(-1));
  featuredNext?.addEventListener("click", () => scrollFeatured(1));
  featuredCarousel?.addEventListener("scroll", updateFeaturedControls, { passive: true });
  window.addEventListener("resize", updateFeaturedControls);
  updateFeaturedControls();

  const navToggle = document.querySelector("[data-nav-toggle]");
  const nav = document.querySelector("[data-primary-nav]");
  navToggle?.addEventListener("click", () => nav?.classList.toggle("open"));

  const filterToggle = document.querySelector("[data-filter-toggle]");
  const filters = document.querySelector(".filters");
  filterToggle?.addEventListener("click", () => {
    const isOpen = filters?.classList.toggle("open");
    filterToggle.textContent = isOpen ? "Hide filters" : "Show filters";
    filterToggle.setAttribute("aria-expanded", String(Boolean(isOpen)));
  });

  const searchToggle = document.querySelector("[data-search-toggle]");
  const searchForm = document.querySelector("[data-search-form]");
  const searchInput = searchForm?.querySelector('input[type="search"]');
  searchToggle?.addEventListener("click", (event) => {
    event.stopPropagation();
    const isOpen = searchForm?.classList.toggle("open");
    searchToggle.setAttribute("aria-expanded", String(Boolean(isOpen)));
    if (isOpen) window.setTimeout(() => searchInput?.focus(), 0);
  });
  searchForm?.addEventListener("click", (event) => event.stopPropagation());
  document.addEventListener("click", () => {
    searchForm?.classList.remove("open");
    searchToggle?.setAttribute("aria-expanded", "false");
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      searchForm?.classList.remove("open");
      searchToggle?.setAttribute("aria-expanded", "false");
      searchToggle?.focus();
    }
  });

  const brandSearch = document.querySelector(".brand-search");
  const brandOptions = [...document.querySelectorAll(".brand-option")];
  const showMoreBrands = document.querySelector("[data-show-more]");
  let allBrandsVisible = false;
  const renderBrandOptions = () => {
    const query = brandSearch?.value.trim().toLowerCase() || "";
    brandOptions.forEach((option, index) => {
      const matches = !query || option.dataset.brandName.includes(query);
      const withinLimit = allBrandsVisible || index < 6 || option.querySelector("input")?.checked;
      option.hidden = !matches || (!query && !withinLimit);
      option.classList.remove("is-collapsed");
    });
    if (showMoreBrands) showMoreBrands.hidden = Boolean(query);
  };
  brandSearch?.addEventListener("input", renderBrandOptions);
  showMoreBrands?.addEventListener("click", () => {
    allBrandsVisible = !allBrandsVisible;
    showMoreBrands.textContent = allBrandsVisible ? "Show fewer brands" : "+ Show all brands";
    showMoreBrands.setAttribute("aria-expanded", String(allBrandsVisible));
    renderBrandOptions();
  });
  renderBrandOptions();

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
