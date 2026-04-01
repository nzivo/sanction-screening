# Sanctions Screening Frontend

Modern React dashboard for managing and screening sanctions lists.

## Features

- **Dashboard**: Overview of all sanctions lists and statistics
- **Screening**: Screen individuals and entities against all sanctions databases
- **Lists Management**: Update and manage sanctions lists (OFAC, UN, EU, UK, FRC Kenya)
- **PEP Management**: Upload and search Politically Exposed Persons
- **World Bank**: Manage World Bank debarred entities
- **FRC Kenya**: Kenya domestic sanctions list management

## Technology Stack

- **React 18**: Modern React with hooks
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **React Router**: Client-side routing
- **Axios**: HTTP client
- **Lucide React**: Beautiful icon set

## Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Configuration

The frontend is configured to proxy API requests to `http://localhost:8000`. If your backend runs on a different port, update `vite.config.js`:

```javascript
export default defineConfig({
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:YOUR_PORT",
        // ...
      },
    },
  },
});
```

## Development

The application runs on `http://localhost:3000` by default.

All API calls are automatically proxied to the backend through the `/api` prefix.

## Project Structure

```
src/
├── components/         # React components
│   ├── Dashboard.jsx
│   ├── Screening.jsx
│   ├── ListsManagement.jsx
│   ├── PEPManagement.jsx
│   ├── WorldBank.jsx
│   └── FRCKenya.jsx
├── services/          # API services
│   └── api.js
├── App.jsx           # Main app component
├── main.jsx          # Entry point
└── index.css         # Global styles
```

## Building for Production

```bash
npm run build
```

The build output will be in the `dist/` directory, ready to be served by any static hosting service.

## Environment Variables

Create a `.env` file if you need to customize the API base URL:

```
VITE_API_BASE_URL=http://your-api-server.com
```

Then update `src/services/api.js` to use `import.meta.env.VITE_API_BASE_URL`.
