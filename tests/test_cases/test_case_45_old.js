function calculateSum(a, b) {
    return a + b;
}

function multiply(x, y) {
    return x * y;
}

function divide(x, y) {
    if (y === 0) {
        throw new Error("Division by zero");
    }
    return x / y;
}

console.log(calculateSum(5, 3));
console.log(multiply(4, 7));
console.log(divide(10, 2));
