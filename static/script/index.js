function togglePassword(fieldId) {
    var inputField = document.getElementById(fieldId);
    var iconToggle = document.getElementById(fieldId + "-icon");
    if (inputField.type === "password") {
        inputField.type = "text";
        iconToggle.classList.remove("fa-eye");
        iconToggle.classList.add("fa-eye-slash");
    } else {
        inputField.type = "password";
        iconToggle.classList.remove("fa-eye-slash");
        iconToggle.classList.add("fa-eye");
    }
}
