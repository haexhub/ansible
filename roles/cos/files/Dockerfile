FROM docker.io/alpine/git:latest as buildStage

WORKDIR /clone-workspace
RUN git clone https://github.com/haexhub/cos.git

FROM docker.io/alpine:latest

RUN set -eux \
    & apk add \
        --no-cache \
        nodejs \
        yarn

WORKDIR /app
COPY --from=buildStage /clone-workspace/cos/ /app
RUN yarn
RUN yarn build

EXPOSE 4173

CMD [ "yarn", "preview", "--host"]
