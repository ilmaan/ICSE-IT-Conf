console.log("Sanity check!");

// Get Stripe publishable key
fetch("/config/")
  .then((result) => {
    return result.json();
  })
  .then((data) => {
    const stripe = Stripe(data.publicKey);

    // document.addEventListener("show-toast", (event) => {
    //   const { level, message, title } = event.detail;
    //   toastr[level](message, title);
    // });

    // Event handler for the registration form
    document.querySelector("#submitPay").addEventListener("click", () => {
      const formData = new FormData(document.querySelector("form"));
      fetch("/registration_info/", {
        method: "POST",
        body: formData,
      })
        .then((response) => response.json())
        .then((data) => {
          console.log("Server Response:", data);
          if (data.success) {
            $("#registerModal").modal("hide");
            $("#paymentModal").modal("show");
          } else {
            alert(data.error || "An error occurred during registration.");
          }
        });
    });

    document.querySelector("#submitPayment").addEventListener("click", () => {
      const email = document.querySelector("#paymentEmail").value;

      // Check payment status before proceeding
      fetch("/check-payment-status/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: email }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.paymentDone) {
            alert("Payment has already been completed for this email.");
          } else {
            fetch("/create-checkout-session/", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({ email: email }),
            })
              .then((result) => result.json())
              .then((data) => {
                console.log("Checkout Session Data:", data);
                if (data.sessionId) {
                  stripe.redirectToCheckout({ sessionId: data.sessionId });
                } else {
                  alert(data.error || "An error occurred during payment.");
                }
              });
          }
        });
    });
  });
