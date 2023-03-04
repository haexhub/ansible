FROM node:18-alpine AS node

FROM alpine

COPY --from=node /usr/lib /usr/lib
COPY --from=node /usr/local/share /usr/local/share
COPY --from=node /usr/local/lib /usr/local/lib
COPY --from=node /usr/local/include /usr/local/include
COPY --from=node /usr/local/bin /usr/local/bin

RUN adduser -S haex
WORKDIR /home/haex/cos
COPY package.json .
RUN chown -R haex /home/haex/
USER haex
RUN npm install
COPY gun.js .

CMD [ "node", "gun.js" ]