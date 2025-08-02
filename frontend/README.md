# 🎨 Feelori AI Assistant Frontend

A modern, production-ready React TypeScript frontend for the Feelori AI WhatsApp Assistant, built with Vite, Tailwind CSS, and featuring the Feelori brand colors.

## ✨ Features

### 🚀 Modern Development Stack
- **Vite** - Lightning-fast development server and build tool
- **TypeScript** - Type safety and enhanced developer experience
- **React 18** - Latest React features with concurrent rendering
- **Tailwind CSS** - Utility-first CSS framework with custom Feelori theme

### 🎯 Performance Optimizations
- **Code Splitting** - Lazy loading of route components for faster initial load
- **Bundle Optimization** - Intelligent chunk splitting and tree shaking
- **Image Optimization** - Responsive images with proper loading strategies
- **Caching Strategy** - Optimized caching for static assets

### 🔒 Security Features
- **Environment Variable Protection** - Backend URL proxied for security
- **CSP Headers** - Content Security Policy implementation
- **XSS Protection** - Cross-site scripting prevention
- **Secure Defaults** - Security-first configuration

### 🎨 Design System
- **Feelori Brand Colors** - Custom color palette (#ff4d6d primary)
- **Glass Morphism** - Modern translucent design elements
- **Responsive Design** - Mobile-first approach with desktop optimization
- **Accessibility** - WCAG compliant with ARIA labels and keyboard navigation

### 🧪 Testing & Quality
- **Vitest** - Fast unit testing with coverage reports
- **React Testing Library** - Component testing best practices
- **ESLint + TypeScript** - Code quality and type checking
- **Husky** - Pre-commit hooks for code quality

## 🏗️ Architecture

### Component Structure
```
src/
├── components/          # Reusable UI components
│   ├── layout/         # Layout components (Sidebar, etc.)
│   ├── tabs/           # Tab components (Dashboard, Products, etc.)
│   └── ui/             # Base UI components (Button, Card, etc.)
├── hooks/              # Custom React hooks
├── lib/                # Utility functions and helpers
├── pages/              # Page components with lazy loading
├── styles/             # Global styles and theme
├── test/               # Test files and setup
└── types/              # TypeScript type definitions
```

### State Management
- **React Query** - Server state management and caching
- **React Hooks** - Local component state management
- **Context API** - Global state for toasts and theme

### Routing & Code Splitting
- **Lazy Loading** - Route-based code splitting for optimal performance
- **Suspense Boundaries** - Proper loading states for async components
- **Error Boundaries** - Graceful error handling with recovery options

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- Yarn (recommended) or npm

### Installation
```bash
# Install dependencies
yarn install

# Start development server
yarn dev

# Build for production
yarn build

# Run tests
yarn test

# Run tests with coverage
yarn test:coverage

# Lint code
yarn lint

# Fix linting issues
yarn lint:fix
```

### Environment Setup
1. Copy `.env.example` to `.env`
2. Configure your environment variables:
```env
VITE_BACKEND_URL=http://localhost:8001
VITE_APP_NAME=Feelori AI Assistant
VITE_APP_VERSION=2.0.0
```

## 🎨 Theme Customization

### Feelori Brand Colors
The app uses a custom Tailwind theme with Feelori brand colors:

```css
:root {
  --feelori-primary: #ff4d6d;    /* Main brand color */
  --feelori-secondary: #c44569;   /* Secondary brand color */
  --feelori-accent: #ff6b88;      /* Accent color */
  --feelori-light: #ffe0e6;       /* Light variant */
  --feelori-dark: #b71c3c;        /* Dark variant */
}
```

### Using Brand Colors
```tsx
// In components
<div className="bg-feelori-primary text-white">
  <h1 className="feelori-gradient-text">Feelori AI</h1>
</div>

// In CSS
.custom-button {
  @apply bg-feelori-primary hover:bg-feelori-dark;
}
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
yarn test

# Run tests in watch mode
yarn test --watch

# Run tests with coverage
yarn test:coverage

# Run tests with UI
yarn test:ui
```

### Test Structure
- **Unit Tests** - Individual component and utility testing
- **Integration Tests** - Multi-component interaction testing
- **E2E Tests** - Full user journey testing (planned)

### Example Test
```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '@/components/ui/button';

test('button renders with correct text', () => {
  render(<Button>Click me</Button>);
  expect(screen.getByText('Click me')).toBeInTheDocument();
});
```

## 📦 Production Build

### Building for Production
```bash
# Create optimized production build
yarn build

# Preview production build locally
yarn preview
```

### Build Optimizations
- **Tree Shaking** - Remove unused code
- **Minification** - Compress JavaScript and CSS
- **Asset Optimization** - Optimize images and fonts
- **Bundle Splitting** - Separate vendor and app code

### Docker Deployment
```bash
# Build Docker image
docker build -f Dockerfile.prod -t feelori-frontend .

# Run container
docker run -p 80:80 feelori-frontend
```

## 🔧 Configuration

### Vite Configuration
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8001',
    },
  },
});
```

### Tailwind Configuration
```javascript
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'feelori': {
          primary: '#ff4d6d',
          secondary: '#c44569',
          // ...more colors
        },
      },
    },
  },
};
```

## 🚀 Performance

### Optimization Strategies
- **Code Splitting** - Lazy load components and routes
- **Bundle Analysis** - Monitor bundle size and composition
- **Caching** - Implement proper caching strategies
- **Image Optimization** - Use WebP and responsive images

### Performance Metrics
- **First Contentful Paint** - < 1.5s
- **Largest Contentful Paint** - < 2.5s
- **Cumulative Layout Shift** - < 0.1
- **First Input Delay** - < 100ms

## 🔒 Security

### Security Measures
- **Environment Variables** - Secure handling of sensitive data
- **CSP Headers** - Content Security Policy implementation
- **Proxy Configuration** - Hide backend URLs from client
- **Dependency Scanning** - Regular security audits

### Security Headers
```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Content-Security-Policy "default-src 'self'" always;
```

## 📈 Monitoring

### Error Tracking
- **Error Boundaries** - Catch and handle React errors
- **Console Logging** - Structured error logging
- **User Feedback** - Toast notifications for user actions

### Performance Monitoring
- **Web Vitals** - Core web vitals tracking
- **Bundle Analysis** - Bundle size monitoring
- **Network Performance** - API response time tracking

## 🤝 Contributing

### Development Workflow
1. **Create Feature Branch** - `git checkout -b feature/new-feature`
2. **Make Changes** - Implement your feature with tests
3. **Run Tests** - Ensure all tests pass
4. **Lint Code** - Fix any linting issues
5. **Submit PR** - Create pull request with description

### Code Standards
- **TypeScript** - Use proper typing for all components
- **ESLint** - Follow established linting rules
- **Prettier** - Consistent code formatting
- **Testing** - Write tests for new features

## 📚 Resources

- [Vite Documentation](https://vitejs.dev/)
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Vitest Documentation](https://vitest.dev/)

## 🆘 Support

For technical support or questions:
- **GitHub Issues** - Report bugs and request features
- **Documentation** - Check the docs for common solutions
- **Team Chat** - Reach out to the development team

---

**Built with ❤️ for Feelori customers using modern web technologies**