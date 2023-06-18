document.addEventListener("DOMContentLoaded", function () {
    const toggleAbstractLinks = document.querySelectorAll('.toggle-abstract');
    const modal = document.getElementById("abstractModal");
    const abstractText = document.getElementById("abstractText");
    const close = document.querySelector(".close");

    toggleAbstractLinks.forEach(link => {
        link.addEventListener('click', function () {
            abstractText.textContent = this.dataset.abstract;
            modal.style.display = "block";
        });
    });

    close.addEventListener("click", function () {
        modal.style.display = "none";
    });

    window.onclick = function (event) {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    }
});
