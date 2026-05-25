const REGISTRATION_FEES = {
  regular: 750,
  src: 650,
  attendee: 550,
  phd: 400,
  secondary: 100,
};

function getRegistrationForm() {
  return (
    document.querySelector("#mainRegistrationForm") ||
    document.querySelector("#secondaryRegistrationForm")
  );
}

function updateMainRegistrationUi() {
  const form = document.querySelector("#mainRegistrationForm");
  if (!form) return;

  const selected = form.querySelector('input[name="registrationType"]:checked');
  const registrationType = selected ? selected.value : "regular";
  const authorFields = document.querySelector("#authorPaperFields");
  const phdFields = document.querySelector("#phdFields");
  const affiliationInput = document.querySelector("#affiliation");
  const feeNote = document.querySelector("#selectedFeeNote");
  const isAttendee = registrationType === "attendee";
  const isPhd = registrationType === "phd";
  const hideAuthorFields = isAttendee || isPhd;

  if (authorFields) {
    authorFields.style.display = hideAuthorFields ? "none" : "block";
    authorFields.querySelectorAll("input").forEach((input) => {
      input.required = !hideAuthorFields;
    });
  }

  if (phdFields) {
    phdFields.style.display = isPhd ? "block" : "none";
  }
  if (affiliationInput) {
    affiliationInput.required = isPhd;
  }

  if (feeNote && REGISTRATION_FEES[registrationType]) {
    feeNote.innerHTML = `Selected fee: <strong>$${REGISTRATION_FEES[registrationType].toFixed(2)}</strong>`;
  }
}

fetch("/config/")
  .then((result) => result.json())
  .then((data) => {
    const stripe = Stripe(data.publicKey);
    const registrationForm = getRegistrationForm();

    document.querySelectorAll(".registration-type").forEach((input) => {
      input.addEventListener("change", updateMainRegistrationUi);
    });
    updateMainRegistrationUi();

    const submitPayButton = document.querySelector("#submitPay");
    if (submitPayButton && registrationForm) {
      submitPayButton.addEventListener("click", () => {
        const formData = new FormData(registrationForm);
        fetch("/registration_info/", {
          method: "POST",
          body: formData,
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              $("#registerModal").modal("hide");
              $("#paymentModal").modal("show");
              const paymentEmail = document.querySelector("#paymentEmail");
              if (paymentEmail) {
                paymentEmail.value = formData.get("email");
              }
            } else {
              alert(data.error || "An error occurred during registration.");
            }
          });
      });
    }

    const submitPaymentButton = document.querySelector("#submitPayment");
    if (submitPaymentButton) {
      submitPaymentButton.addEventListener("click", () => {
        const email = document.querySelector("#paymentEmail").value.trim().toLowerCase();
        if (!email) {
          alert("Please enter your email.");
          return;
        }

        fetch("/check-payment-status/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.paymentDone) {
              alert("Payment has already been completed for this email.");
              return;
            }
            if (data.error) {
              alert(data.error);
              return;
            }

            const fee = data.fee ? ` ($${Number(data.fee).toFixed(2)})` : "";
            if (!window.confirm(`Proceed to Stripe checkout${fee}?`)) {
              return;
            }

            fetch("/create-checkout-session/", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ email }),
            })
              .then((result) => result.json())
              .then((checkoutData) => {
                if (checkoutData.sessionId) {
                  stripe.redirectToCheckout({ sessionId: checkoutData.sessionId });
                } else {
                  alert(checkoutData.error || "An error occurred during payment.");
                }
              });
          });
      });
    }
  });
