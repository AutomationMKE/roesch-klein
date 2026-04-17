// Roesch & Klein — client-side filter + gallery
(function () {
  "use strict";

  // ---------- Homepage filter ----------
  var grid = document.getElementById("listing-grid");
  if (grid) {
    var cards = Array.prototype.slice.call(grid.querySelectorAll(".card"));
    var fCity = document.getElementById("f-city");
    var fType = document.getElementById("f-type");
    var fPmin = document.getElementById("f-pmin");
    var fPmax = document.getElementById("f-pmax");
    var fReset = document.getElementById("f-reset");
    var resultCount = document.getElementById("result-count");
    var emptyState = document.getElementById("empty-state");
    var segBtns = Array.prototype.slice.call(document.querySelectorAll(".seg-btn"));
    var mode = "all";

    function applyFilter() {
      var city = (fCity && fCity.value) || "";
      var type = (fType && fType.value) || "";
      var pmin = parseInt((fPmin && fPmin.value) || "", 10);
      var pmax = parseInt((fPmax && fPmax.value) || "", 10);
      if (isNaN(pmin)) pmin = -Infinity;
      if (isNaN(pmax)) pmax = Infinity;

      var visible = 0;
      cards.forEach(function (c) {
        var cMode = c.getAttribute("data-mode");
        var cCity = c.getAttribute("data-city");
        var cType = c.getAttribute("data-type");
        var cPriceRaw = c.getAttribute("data-price");
        var cPrice = cPriceRaw ? parseInt(cPriceRaw, 10) : null;

        var match = true;
        if (mode !== "all" && cMode !== mode) match = false;
        if (city && cCity !== city) match = false;
        if (type && cType !== type) match = false;
        if (cPrice !== null) {
          if (cPrice < pmin || cPrice > pmax) match = false;
        } else {
          // Listings without numeric price are hidden when a price filter is active
          if (pmin !== -Infinity || pmax !== Infinity) match = false;
        }

        c.style.display = match ? "" : "none";
        if (match) visible++;
      });

      if (resultCount) resultCount.textContent = visible;
      if (emptyState) emptyState.hidden = visible !== 0;
      grid.style.display = visible === 0 ? "none" : "";
    }

    segBtns.forEach(function (b) {
      b.addEventListener("click", function () {
        segBtns.forEach(function (x) { x.classList.remove("is-active"); });
        b.classList.add("is-active");
        mode = b.getAttribute("data-value");
        applyFilter();
      });
    });

    [fCity, fType, fPmin, fPmax].forEach(function (el) {
      if (!el) return;
      el.addEventListener("input", applyFilter);
      el.addEventListener("change", applyFilter);
    });

    if (fReset) {
      fReset.addEventListener("click", function () {
        if (fCity) fCity.value = "";
        if (fType) fType.value = "";
        if (fPmin) fPmin.value = "";
        if (fPmax) fPmax.value = "";
        mode = "all";
        segBtns.forEach(function (x) { x.classList.remove("is-active"); });
        var allBtn = document.querySelector('.seg-btn[data-value="all"]');
        if (allBtn) allBtn.classList.add("is-active");
        applyFilter();
      });
    }
  }

  // ---------- Detail-page gallery ----------
  var galleryHero = document.getElementById("gallery-hero");
  if (galleryHero) {
    var thumbs = Array.prototype.slice.call(document.querySelectorAll(".thumb"));
    thumbs.forEach(function (t) {
      t.addEventListener("click", function () {
        thumbs.forEach(function (x) { x.classList.remove("is-active"); });
        t.classList.add("is-active");
        var src = t.getAttribute("data-src");
        if (src) galleryHero.src = src;
      });
    });

    // Keyboard nav
    document.addEventListener("keydown", function (e) {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      var active = document.querySelector(".thumb.is-active");
      if (!active) return;
      var idx = thumbs.indexOf(active);
      var next = e.key === "ArrowRight" ? idx + 1 : idx - 1;
      if (next >= 0 && next < thumbs.length) thumbs[next].click();
    });
  }
})();
