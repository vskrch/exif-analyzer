/**
 * EXIF Analyzer - Client-side Application Logic
 */
(function () {
    "use strict";

    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("fileInput");
    const previewSection = document.getElementById("previewSection");
    const imagePreview = document.getElementById("imagePreview");
    const exifData = document.getElementById("exifData");
    const imageMeta = document.getElementById("imageMeta");
    const errorBox = document.getElementById("errorBox");

    // --- Drag & Drop ---
    dropZone.addEventListener("dragover", function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove("dragover");
        var files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    dropZone.addEventListener("click", function (e) {
        if (e.target.tagName !== "BUTTON") {
            fileInput.click();
        }
    });

    fileInput.addEventListener("change", function (e) {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    // --- File Handling ---
    function handleFile(file) {
        if (!file.type.startsWith("image/")) {
            showError("Please upload an image file.");
            return;
        }

        hideError();
        previewSection.classList.add("active");
        imagePreview.src = URL.createObjectURL(file);

        // Show image metadata
        var sizeKB = (file.size / 1024).toFixed(1);
        var sizeDisplay = sizeKB > 1024
            ? (file.size / (1024 * 1024)).toFixed(2) + " MB"
            : sizeKB + " KB";
        imageMeta.textContent = file.name + " (" + sizeDisplay + ")";

        exifData.innerHTML = '<div class="loading">Analyzing EXIF data</div>';

        var formData = new FormData();
        formData.append("file", file);

        fetch("/analyze", {
            method: "POST",
            body: formData,
        })
            .then(function (response) {
                return response.json().then(function (data) {
                    return { ok: response.ok, data: data };
                });
            })
            .then(function (result) {
                if (result.ok) {
                    displayExifData(result.data);
                } else {
                    var msg =
                        (result.data.error && result.data.error.message) ||
                        result.data.detail ||
                        "Error analyzing image";
                    showError(msg);
                }
            })
            .catch(function (err) {
                showError("Network error: " + err.message);
            });
    }

    // --- Display ---
    function displayExifData(data) {
        if (!data.categorized || Object.keys(data.categorized).length === 0) {
            exifData.innerHTML =
                '<div class="no-data">No EXIF metadata found in this image.</div>';
            return;
        }

        var html = "";
        var categories = Object.entries(data.categorized);

        categories.forEach(function (entry) {
            var category = entry[0];
            var items = entry[1];
            var contentId = "cat-" + category.replace(/[^a-zA-Z0-9]/g, "-");

            html +=
                '<div class="info-card">' +
                '<h3 onclick="window.toggleCategory(\'' + contentId + '\', this)">' +
                '<span>' + category + ' <span class="count">(' + items.length + ')</span></span>' +
                '<span class="toggle-icon">&#9662;</span>' +
                "</h3>" +
                '<div class="category-content" id="' + contentId + '">';

            items.forEach(function (item) {
                html +=
                    '<div class="info-row">' +
                    '<span class="info-label">' + escapeHtml(item.tag) + "</span>" +
                    '<span class="info-value">' + escapeHtml(item.value) + "</span>" +
                    "</div>";
            });

            html += "</div></div>";
        });

        exifData.innerHTML = html;
    }

    // --- Utilities ---
    window.toggleCategory = function (id, header) {
        var content = document.getElementById(id);
        var icon = header.querySelector(".toggle-icon");
        content.classList.toggle("collapsed");
        icon.classList.toggle("collapsed");
    };

    function showError(message) {
        errorBox.textContent = message;
        errorBox.classList.add("active");
    }

    function hideError() {
        errorBox.classList.remove("active");
        errorBox.textContent = "";
    }

    function escapeHtml(text) {
        var div = document.createElement("div");
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }
})();
