FROM node:20-slim

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

# Install all dependencies including devDependencies (tailwindcss, @tailwindcss/postcss, typescript)
COPY package.json ./
RUN npm install

COPY . .
RUN mkdir -p /app/public

ARG NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
ARG NEXT_PUBLIC_API_KEY=""
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_KEY=$NEXT_PUBLIC_API_KEY

RUN npm run build

ENV NODE_ENV=production
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["npx", "next", "start", "-H", "0.0.0.0", "-p", "3000"]