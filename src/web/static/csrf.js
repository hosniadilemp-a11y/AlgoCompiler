(function () {
    const csrfToken = window.APP_CSRF_TOKEN;
    if (!csrfToken || typeof window.fetch !== 'function') {
        return;
    }

    const originalFetch = window.fetch.bind(window);

    function isUnsafeMethod(method) {
        return ['POST', 'PUT', 'PATCH', 'DELETE'].includes(String(method || 'GET').toUpperCase());
    }

    function isSameOrigin(target) {
        try {
            const url = typeof target === 'string' ? new URL(target, window.location.href) : new URL(target.url, window.location.href);
            return url.origin === window.location.origin;
        } catch (error) {
            return true;
        }
    }

    window.fetch = function (input, init = {}) {
        const requestMethod = typeof Request !== 'undefined' && input instanceof Request ? input.method : 'GET';
        const method = (init.method || requestMethod || 'GET').toUpperCase();
        if (!isUnsafeMethod(method) || !isSameOrigin(input)) {
            return originalFetch(input, init);
        }

        const requestHeaders = typeof Request !== 'undefined' && input instanceof Request ? input.headers : undefined;
        const headers = new Headers(init.headers || requestHeaders || {});
        if (!headers.has('X-CSRF-Token')) {
            headers.set('X-CSRF-Token', csrfToken);
        }

        return originalFetch(input, { ...init, headers });
    };
})();
