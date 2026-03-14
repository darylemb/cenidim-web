# Cenidim Web - Frontend

This directory contains the user interface for the Cenidim Web Application, built with **React**.

## Features

- **Institutional Design System**: Faithfully replicates the required visual identity with precise typography and colors (Guinda `#751428` and Gold `#C5A46C`).
- **Search Engine (Canciones)**: Dynamically fetches data from the Python backend to filter through albums, track names, and lyrics without reloading the page. Features an elegant modal to display full song lyrics.
- **Analytics Dashboards**: Integrates `Chart.js` to visualize overall database metrics. This module acts as the foundation to display AI/NLP sentiment analysis data in the future.

## Available Scripts

In the project directory, you can run:

### `npm start`
Runs the application in development mode.
Open [http://localhost:3000](http://localhost:3000) to view it in your browser. 
*Note: Any unknown requests made by the frontend are automatically proxied to the backend at `http://localhost:8000` thanks to the `proxy` field configured in `package.json`.*

### `npm run build`
Builds the app for production to the `build` folder.
It correctly bundles React in production mode and optimizes the build for best performance and minified files.

### `npm test`
Launches the test runner in interactive watch mode.

## Docker Deployment

A `Dockerfile.frontend` configuration is included to build the static React bundle using a multi-stage process. The final compiled assets are served using a lightweight **Nginx** web server. 

For standard deployment, it is highly recommended to use the `docker-compose.yml` file located in the root directory to orchestrate both the frontend and backend services simultaneously.
