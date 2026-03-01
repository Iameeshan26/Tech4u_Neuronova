/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'neuronova-dark': '#0f172a',
                'neuronova-blue': '#3b82f6',
                'neuronova-accent': '#10b981',
            }
        },
    },
    plugins: [],
}
