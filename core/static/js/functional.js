document.addEventListener("DOMContentLoaded", function () {
  // Mobile menu toggle
  const hamburger = document.querySelector(".hamburger");
  const menu = document.querySelector(".menu");

  if (hamburger) {
    hamburger.addEventListener("click", function () {
      menu.classList.toggle("show");
    });
  }

  // Card flip functionality
  const flipLabels = document.querySelectorAll(".flip-label");

  flipLabels.forEach((label) => {
    label.addEventListener("click", function () {
      const cardId = this.getAttribute("data-card");
      const card = document.getElementById(cardId);

      if (card.style.transform === "rotateY(180deg)") {
        card.style.transform = "rotateY(0deg)";
        this.textContent = "Back Side";
        card.classList.remove("clicked");
      } else {
        card.style.transform = "rotateY(180deg)";
        this.textContent = "Front Side";
        card.classList.add("clicked");
      }
    });
  });

  // Card hover effect with touch device detection
  const cards = document.querySelectorAll(".business-card");

  // Touch device detection
  const isTouchDevice = () => {
    return (
      "ontouchstart" in window ||
      navigator.maxTouchPoints > 0 ||
      navigator.msMaxTouchPoints > 0
    );
  };

  if (!isTouchDevice()) {
    // Only apply hover effects on non-touch devices
    cards.forEach((card) => {
      const wrapper = card.closest(".business-card-wrapper");

      wrapper.addEventListener("mouseenter", function () {
        if (!card.classList.contains("clicked")) {
          card.style.transform = "rotateY(180deg)";
          this.querySelector(".flip-label").textContent = "Front Side";
        }
      });

      wrapper.addEventListener("mouseleave", function () {
        if (!card.classList.contains("clicked")) {
          card.style.transform = "rotateY(0deg)";
          this.querySelector(".flip-label").textContent = "Back Side";
        }
      });
    });
  }

  // State, County, City dependent dropdown simulation
  const stateSelect = document.getElementById("state");
  if (stateSelect) {
    stateSelect.addEventListener("change", function () {
      const countySelect = document.getElementById("county");
      if (this.value) {
        countySelect.removeAttribute("disabled");
        countySelect.innerHTML = `
                    <option value="">Select County</option>
                    <option value="county1">County 1</option>
                    <option value="county2">County 2</option>
                    <option value="county3">County 3</option>
                `;
      } else {
        countySelect.setAttribute("disabled", "disabled");
        countySelect.innerHTML = '<option value="">Select County</option>';
        document.getElementById("city").setAttribute("disabled", "disabled");
        document.getElementById("city").innerHTML =
          '<option value="">Select City</option>';
      }
    });
  }

  const countySelect = document.getElementById("county");
  if (countySelect) {
    countySelect.addEventListener("change", function () {
      const citySelect = document.getElementById("city");
      if (this.value) {
        citySelect.removeAttribute("disabled");
        citySelect.innerHTML = `
                    <option value="">Select City</option>
                    <option value="city1">City 1</option>
                    <option value="city2">City 2</option>
                    <option value="city3">City 3</option>
                `;
      } else {
        citySelect.setAttribute("disabled", "disabled");
        citySelect.innerHTML = '<option value="">Select City</option>';
      }
    });
  }
});
