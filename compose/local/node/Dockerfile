FROM node:20-bullseye-slim

WORKDIR /app

COPY ./package.json /app

RUN npm install -g npm@latest

RUN npm install && npm cache clean --force

ENV PATH ./node_modules/.bin/:$PATH
