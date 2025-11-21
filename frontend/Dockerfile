FROM node:20

WORKDIR /app

# Копируем package.json и package-lock.json (если есть)
COPY package*.json ./

# Используем npm install вместо npm ci
RUN npm install

# Копируем остальной код
COPY . .

EXPOSE 3000

# Запуск dev-сервера Vite
CMD ["npm", "run", "dev", "--", "--host"]