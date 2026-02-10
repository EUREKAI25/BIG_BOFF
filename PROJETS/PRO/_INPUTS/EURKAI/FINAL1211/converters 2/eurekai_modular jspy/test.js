
/**
 * Additionne deux nombres
 * @param {number} a
 * @param {number} b
 * @returns {number}
 */
function add(a, b) {
    return a + b;
}

/**
 * Salue quelqu'un
 * @param {string} name
 * @returns {string}
 */
function greet(name) {
    return "Hello, " + name + "!";
}

window.add = add;
window.greet = greet;
