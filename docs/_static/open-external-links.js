// Open all external links in a new tab
document.addEventListener("DOMContentLoaded", function () {
    var links = document.querySelectorAll("a[href]");
    links.forEach(function (link) {
        if (link.hostname && link.hostname !== window.location.hostname) {
            link.setAttribute("target", "_blank");
            link.setAttribute("rel", "noopener noreferrer");
        }
    });
});
