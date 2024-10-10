ARG NODE_VERSION=20.0.0

FROM node:${NODE_VERSION}-alpine

# Use production node environment by default.
ENV NODE_ENV production

WORKDIR /app

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.npm to speed up subsequent builds.
# Leverage a bind mounts to package.json and package-lock.json to avoid having to copy them into
# into this layer.
#RUN --mount=type=bind, source=package.json, target=package.json \
#    --mount=type=bind, source=package-lock.json, target=package-lock.json \
#    --mount=type=cache, target=/root/.npm \
#    npm ci --omit=dev && \
#    npm install serve

RUN npm install serve
# Run the application as a non-root user.
USER node

COPY .output/public  .

EXPOSE 3000

# Run the application.
CMD npx serve .
