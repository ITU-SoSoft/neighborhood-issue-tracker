/**
 * Storage utilities with proper error handling for restricted browser environments
 * (e.g., Gmail in-app browser, embedded webviews, private browsing mode)
 */

export interface StorageStatus {
  localStorageAvailable: boolean;
  sessionStorageAvailable: boolean;
  cookiesEnabled: boolean;
  isEmbeddedBrowser: boolean;
  userAgent: string;
}

/**
 * Check if localStorage is available and writable
 */
export function isLocalStorageAvailable(): boolean {
  if (typeof window === "undefined") return false;

  try {
    const testKey = "__storage_test__";
    window.localStorage.setItem(testKey, testKey);
    window.localStorage.removeItem(testKey);
    return true;
  } catch {
    return false;
  }
}

/**
 * Check if sessionStorage is available and writable
 */
export function isSessionStorageAvailable(): boolean {
  if (typeof window === "undefined") return false;

  try {
    const testKey = "__storage_test__";
    window.sessionStorage.setItem(testKey, testKey);
    window.sessionStorage.removeItem(testKey);
    return true;
  } catch {
    return false;
  }
}

/**
 * Check if cookies are enabled
 */
export function areCookiesEnabled(): boolean {
  if (typeof document === "undefined") return false;

  try {
    document.cookie = "cookietest=1; SameSite=Strict";
    const result = document.cookie.indexOf("cookietest=") !== -1;
    document.cookie =
      "cookietest=1; expires=Thu, 01-Jan-1970 00:00:01 GMT; SameSite=Strict";
    return result;
  } catch {
    return false;
  }
}

/**
 * Detect if running in an embedded browser (Gmail, Facebook, Instagram, etc.)
 */
export function isEmbeddedBrowser(): boolean {
  if (typeof navigator === "undefined") return false;

  const ua = navigator.userAgent.toLowerCase();

  // Common embedded browser signatures
  const embeddedSignatures = [
    "fban", // Facebook App
    "fbav", // Facebook App Version
    "instagram", // Instagram
    "twitter", // Twitter
    "line", // Line
    "wv", // Android WebView
    "gsa", // Google Search App
    "webview", // Generic WebView
    "micromessenger", // WeChat
    "snapchat", // Snapchat
    "linkedin", // LinkedIn
    "pinterest", // Pinterest
  ];

  // Check for iOS embedded browsers
  const isIOSWebView = /(iphone|ipod|ipad).*applewebkit(?!.*safari)/i.test(
    navigator.userAgent,
  );

  return embeddedSignatures.some((sig) => ua.includes(sig)) || isIOSWebView;
}

/**
 * Get comprehensive storage status for debugging
 */
export function getStorageStatus(): StorageStatus {
  return {
    localStorageAvailable: isLocalStorageAvailable(),
    sessionStorageAvailable: isSessionStorageAvailable(),
    cookiesEnabled: areCookiesEnabled(),
    isEmbeddedBrowser: isEmbeddedBrowser(),
    userAgent:
      typeof navigator !== "undefined" ? navigator.userAgent : "unknown",
  };
}

/**
 * Safe localStorage getItem with fallback
 */
export function safeGetItem(key: string): string | null {
  if (!isLocalStorageAvailable()) {
    console.warn(`[Storage] localStorage not available, cannot get "${key}"`);
    return null;
  }

  try {
    return window.localStorage.getItem(key);
  } catch (error) {
    console.error(`[Storage] Failed to get "${key}":`, error);
    return null;
  }
}

/**
 * Safe localStorage setItem with error handling
 */
export function safeSetItem(key: string, value: string): boolean {
  if (!isLocalStorageAvailable()) {
    console.warn(`[Storage] localStorage not available, cannot set "${key}"`);
    return false;
  }

  try {
    window.localStorage.setItem(key, value);
    return true;
  } catch (error) {
    console.error(`[Storage] Failed to set "${key}":`, error);
    return false;
  }
}

/**
 * Safe localStorage removeItem with error handling
 */
export function safeRemoveItem(key: string): boolean {
  if (!isLocalStorageAvailable()) {
    console.warn(
      `[Storage] localStorage not available, cannot remove "${key}"`,
    );
    return false;
  }

  try {
    window.localStorage.removeItem(key);
    return true;
  } catch (error) {
    console.error(`[Storage] Failed to remove "${key}":`, error);
    return false;
  }
}

/**
 * Log storage diagnostics to console (useful for debugging)
 */
export function logStorageDiagnostics(): void {
  const status = getStorageStatus();

  console.group("📦 Storage Diagnostics");
  console.log("localStorage available:", status.localStorageAvailable);
  console.log("sessionStorage available:", status.sessionStorageAvailable);
  console.log("Cookies enabled:", status.cookiesEnabled);
  console.log("Embedded browser detected:", status.isEmbeddedBrowser);
  console.log("User Agent:", status.userAgent);
  console.groupEnd();
}
