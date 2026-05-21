document.addEventListener("DOMContentLoaded", function () {
    document.documentElement.classList.add("js-enabled");
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function animateCounter(counter) {
        if (counter.dataset.counted === "true") return;

        counter.dataset.counted = "true";
        const target = Number(counter.dataset.count || "0");
        const initialText = counter.textContent.trim();
        const suffix = initialText.includes("%") ? "%" : (initialText.includes("+") ? "+" : "");

        if (prefersReducedMotion) {
            counter.textContent = `${target}${suffix}`;
            return;
        }

        const duration = 1100;
        const startTime = performance.now();

        function update(now) {
            const progress = Math.min((now - startTime) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            counter.textContent = `${Math.round(target * eased)}${suffix}`;

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                counter.textContent = `${target}${suffix}`;
            }
        }

        requestAnimationFrame(update);
    }

    const revealSelectors = [
        ".landing-hero",
        ".landing-section",
        ".landing-card",
        ".stat-card-modern",
        ".testimonial-card"
    ];

    const revealElements = Array.from(document.querySelectorAll(revealSelectors.join(",")))
        .filter(function (element) {
            return !element.closest(".dashboard-sidebar, .dashboard-overlay, dialog, [role='dialog'], .modal");
        });

    revealElements.forEach(function (element) {
        element.classList.add("reveal");
        element.classList.add("reveal-managed");
    });

    const staggerContainers = [
        ".landing-card-grid",
        ".category-grid",
        ".benefit-grid",
        ".trending-grid",
        ".testimonial-grid",
        ".stats-grid-modern",
        ".gamification-cards"
    ];

    document.querySelectorAll(staggerContainers.join(",")).forEach(function (container) {
        Array.from(container.children).forEach(function (child, index) {
            if (child.classList.contains("reveal")) {
                child.classList.add("reveal-delay-" + ((index % 4) + 1));
            }
        });
    });

    if (prefersReducedMotion || !("IntersectionObserver" in window)) {
        revealElements.forEach(function (element) {
            element.classList.add("visible");
            element.classList.add("reveal-visible");
        });
        document.querySelectorAll(".counter[data-count]").forEach(animateCounter);
        return;
    }

    const observer = new IntersectionObserver(function (entries, observerInstance) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
                entry.target.classList.add("reveal-visible");
                observerInstance.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.12
    });

    revealElements.forEach(function (element) {
        observer.observe(element);
    });

    const counterObserver = new IntersectionObserver(function (entries, observerInstance) {
        entries.forEach(function (entry) {
            if (!entry.isIntersecting) return;
            animateCounter(entry.target);
            observerInstance.unobserve(entry.target);
        });
    }, {
        threshold: 0.55
    });

    document.querySelectorAll(".counter[data-count]").forEach(function (counter) {
        counterObserver.observe(counter);
    });

    const hero = document.querySelector(".parallax-hero");
    const heroImage = hero ? hero.querySelector(".hero-community-image") : null;

    if (hero && heroImage) {
        let ticking = false;

        function updateHeroParallax() {
            const rect = hero.getBoundingClientRect();
            const viewportHeight = window.innerHeight || document.documentElement.clientHeight;

            if (rect.bottom < 0 || rect.top > viewportHeight) {
                ticking = false;
                return;
            }

            const progress = (viewportHeight - rect.top) / (viewportHeight + rect.height);
            const clamped = Math.max(0, Math.min(1, progress));
            const imageOffset = (clamped - 0.5) * 18;
            const bgOffset = (clamped - 0.5) * 8;

            hero.style.setProperty("--hero-parallax-y", `${imageOffset.toFixed(2)}px`);
            hero.style.setProperty("--hero-bg-y", `${bgOffset.toFixed(2)}px`);
            ticking = false;
        }

        function requestHeroParallax() {
            if (ticking) return;
            ticking = true;
            requestAnimationFrame(updateHeroParallax);
        }

        updateHeroParallax();
        window.addEventListener("scroll", requestHeroParallax, { passive: true });
        window.addEventListener("resize", requestHeroParallax);
    }
});
