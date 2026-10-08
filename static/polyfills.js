(function () {
  function defineAtPolyfill(ctor) {
    if (typeof ctor === "undefined" || ctor.prototype.at) {
      return;
    }

    Object.defineProperty(ctor.prototype, "at", {
      value: function at(index) {
        var length = this.length >>> 0;
        if (length === 0) {
          return undefined;
        }

        var normalizedIndex = Number(index) || 0;
        if (normalizedIndex < 0) {
          normalizedIndex += length;
        }

        if (normalizedIndex < 0 || normalizedIndex >= length) {
          return undefined;
        }

        return this[normalizedIndex];
      },
      writable: true,
      configurable: true,
    });
  }

  defineAtPolyfill(Array);
  defineAtPolyfill(String);
  defineAtPolyfill(Int8Array);
  defineAtPolyfill(Uint8Array);
  defineAtPolyfill(Uint8ClampedArray);
  defineAtPolyfill(Int16Array);
  defineAtPolyfill(Uint16Array);
  defineAtPolyfill(Int32Array);
  defineAtPolyfill(Uint32Array);
  defineAtPolyfill(Float32Array);
  defineAtPolyfill(Float64Array);
  defineAtPolyfill(typeof BigInt64Array === "undefined" ? undefined : BigInt64Array);
  defineAtPolyfill(typeof BigUint64Array === "undefined" ? undefined : BigUint64Array);

  if (!String.prototype.replaceAll) {
    Object.defineProperty(String.prototype, "replaceAll", {
      value: function replaceAll(searchValue, replaceValue) {
        if (searchValue instanceof RegExp) {
          if (!searchValue.global) {
            throw new TypeError("`replaceAll` requires a global regular expression.");
          }
          return this.replace(searchValue, replaceValue);
        }

        return this.split(String(searchValue)).join(String(replaceValue));
      },
      writable: true,
      configurable: true,
    });
  }
})();
