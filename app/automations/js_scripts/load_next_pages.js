(() => {
    if (typeof LoadNextPages === 'function') {
        // Try to load all pages at once
        for (let i = 0; i < 100; i++) {
            LoadNextPages(5);
        }
        return true;
    }
    return false;
})();