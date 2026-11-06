/* Subtle 3D tilt for elements with class "tilt".
   Disabled for touch screens and for users who prefer reduced motion. */
(function () {
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var finePointer = window.matchMedia("(pointer: fine)").matches;
    if (reduce || !finePointer) return;

    document.querySelectorAll(".tilt").forEach(function (card) {
        var max = parseFloat(card.dataset.tilt || "8");
        var frame = null;

        card.addEventListener("pointermove", function (event) {
            var rect = card.getBoundingClientRect();
            var x = (event.clientX - rect.left) / rect.width - 0.5;
            var y = (event.clientY - rect.top) / rect.height - 0.5;
            if (frame) cancelAnimationFrame(frame);
            frame = requestAnimationFrame(function () {
                card.style.transform =
                    "perspective(900px) rotateX(" + (-y * max).toFixed(2) + "deg) rotateY(" +
                    (x * max).toFixed(2) + "deg) translateZ(0)";
                card.style.setProperty("--glare-x", ((x + 0.5) * 100).toFixed(1) + "%");
                card.style.setProperty("--glare-y", ((y + 0.5) * 100).toFixed(1) + "%");
            });
        });
        card.addEventListener("pointerleave", function () {
            if (frame) cancelAnimationFrame(frame);
            card.style.transform = "";
        });
    });
})();
