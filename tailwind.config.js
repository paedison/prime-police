/** @type {import('tailwindcss').Config} */
module.exports = {
  prefix: "tw-",
  content: [
    "../templates/**/*.html",
    "../**/templates/**/*.html",
    "../**/forms.py",
  ],
  theme: {
    extend: {},
  },
};
