// Test bootstrap for Vitest (jsdom). Adds the jest-dom matchers used by the component tests.
import '@testing-library/jest-dom/vitest'

// jsdom implements neither of these; the layout/charts need them both.
if (!window.matchMedia) {
  window.matchMedia = (query) => ({ matches: false, media: query, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {}, dispatchEvent() {} })
}
if (!globalThis.ResizeObserver) {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
}

