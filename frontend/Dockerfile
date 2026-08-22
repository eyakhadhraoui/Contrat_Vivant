# ==========================================
# Multi-stage Dockerfile - Frontend React + Vite
# ==========================================

# Étape 1 : Build de l'application React
FROM node:20-alpine AS builder

WORKDIR /app

# Copie des fichiers de dépendances
COPY package.json package-lock.json* ./

# Installation des dépendances
RUN npm ci || npm install

# Copie du code source du frontend
COPY . .

# Construction des fichiers statiques de production (dist)
RUN npm run build

# Étape 2 : Image de production Nginx
FROM nginx:1.25-alpine

# Suppression de la configuration Nginx par défaut
RUN rm -rf /etc/nginx/conf.d/default.conf

# Copie de notre configuration Nginx personnalisée
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copie du build React produit à l'étape 1
COPY --from=builder /app/dist /usr/share/nginx/html

# Port exposé
EXPOSE 80

# Démarrage de Nginx
CMD ["nginx", "-g", "daemon off;"]
