# Starten Sie mit dem offiziellen n8n-Image als Basis.
# Es wird empfohlen, eine spezifische Version zu verwenden, z.B. n8nio/n8n:1.25.0
FROM docker.n8n.io/n8nio/n8n

# Wechseln Sie zum root-Benutzer, um globale Installationsberechtigungen zu erhalten.
USER root

# Installieren Sie die benötigten externen npm-Pakete global.
# Fügen Sie hier alle Bibliotheken hinzu, die Sie im Code-Node verwenden möchten.
RUN npm install -g playwright

# Wechseln Sie aus Sicherheitsgründen zurück zum unprivilegierten 'node'-Benutzer.
# Dies stellt sicher, dass der n8n-Prozess mit minimalen Rechten läuft.
USER node