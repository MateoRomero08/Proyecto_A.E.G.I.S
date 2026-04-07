import React from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { Toaster } from 'sonner'
// Entramos a la carpeta app para encontrar el archivo routes.tsx
import { router } from './app/routes' 
// Buscamos la carpeta styles que está al mismo nivel que este archivo
import './styles/index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
    <Toaster richColors position="top-right" closeButton />
  </React.StrictMode>
)