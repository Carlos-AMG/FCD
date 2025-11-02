() => {
    const urls = [];

    // First priority: Get from DOM in order (already loaded images)
    const domImages = document.querySelectorAll('#divImage img');
    const domUrls = [];

    for (let img of domImages) {
        const src = img.getAttribute('src');
        if (src &&
            !src.includes('blank.gif') &&
            !src.includes('trans.png') &&
            !src.includes('loading.gif')) {
            domUrls.push(src);
        } else {
            // Push null for placeholder images to maintain order
            domUrls.push(null);
        }
    }

    // Second priority: Get from JavaScript array (for lazy-loaded images)
    let jsUrls = [];
    if (typeof _q1HQcHOD6h8 !== 'undefined' && Array.isArray(_q1HQcHOD6h8)) {
        for (let encoded of _q1HQcHOD6h8) {
            try {
                if (typeof cWgp3Ezg9eE === 'function') {
                    const decoded = cWgp3Ezg9eE(5, encoded);
                    if (decoded && decoded.includes('http')) {
                        jsUrls.push(decoded);
                    }
                } else {
                    // Fallback URL construction
                    const baseUrl = 'https://2.bp.blogspot.com/pw/AP1Gcz';
                    jsUrls.push(baseUrl + encoded);
                }
            } catch (e) {
                console.error('Error decoding URL:', e);
            }
        }
    }

    // Merge URLs: Use DOM URLs where available, fill gaps with JS array URLs
    let jsIndex = 0;
    for (let i = 0; i < domUrls.length; i++) {
        if (domUrls[i]) {
            urls.push(domUrls[i]);
        } else if (jsIndex < jsUrls.length) {
            // Fill placeholder with JS URL
            urls.push(jsUrls[jsIndex]);
            jsIndex++;
        }
    }

    // Add any remaining JS URLs that weren't used
    while (jsIndex < jsUrls.length) {
        urls.push(jsUrls[jsIndex]);
        jsIndex++;
    }

    // Remove any remaining nulls and duplicates while preserving order
    const finalUrls = [];
    const seen = new Set();
    for (const url of urls) {
        if (url && !seen.has(url)) {
            finalUrls.push(url);
            seen.add(url);
        }
    }

    return finalUrls;
}