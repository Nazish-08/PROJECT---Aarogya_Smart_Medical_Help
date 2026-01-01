// JavaScript for Aarogya – Modals, map, interactivity

// Example: Show medicine info in modal
function showMedicineInfo(name, dosage, sideEffects) {
    document.getElementById('med-name').innerText = name;
    document.getElementById('med-dosage').innerText = dosage;
    document.getElementById('med-side-effects').innerText = sideEffects;
    let modal = new bootstrap.Modal(document.getElementById('medicineModal'));
    modal.show();
}
